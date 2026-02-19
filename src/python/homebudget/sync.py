"""SyncUpdate payload encoding and persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import json
import sqlite3
import uuid
import zlib
from pathlib import Path
from typing import Any

from homebudget.models import ExpenseRecord, IncomeRecord
from homebudget.schema import FLAG_Y

# SyncUpdate payload encoding constants
ZLIB_COMPRESSION_LEVEL = 9  # Maximum compression
ZLIB_WBITS = 15  # Full zlib format with header and checksum
UPDATE_TYPE_ANY = "Any"


@dataclass(frozen=True)
class DeviceInfoRecord:
    key: int
    device_id: str


class SyncUpdateManager:
    """Create SyncUpdate entries for HomeBudget operations.
    
    This class uses a configuration-driven approach where all payload structures,
    field types, and compression settings are defined in sync-config.json.
    This eliminates hard-coded payload logic and makes it trivial to add new
    resource types by just updating the configuration.
    """

    def __init__(self, connection: sqlite3.Connection | None, config_path: Path | None = None) -> None:
        """Initialize with an existing database connection and load sync configuration.
        
        Args:
            connection: Active database connection
            config_path: Optional path to sync-config.json. If not provided, uses default location.
        """
        if connection is None:
            raise RuntimeError("Connection is required for sync updates")
        self.connection = connection
        
        # Load sync configuration
        if config_path is None:
            # Default: sync-config.json packaged alongside this module
            config_path = Path(__file__).with_name("sync-config.json")
        
        with config_path.open("r", encoding="utf-8") as f:
            self.config = json.load(f)
        
        # Build resource type mapping for quick lookup
        self._resource_map = {
            "ExpenseRecord": "expense",
            "IncomeRecord": "income",
        }

    def _get_resource_type(self, record: ExpenseRecord | IncomeRecord) -> str:
        """Determine resource type from record class name."""
        class_name = type(record).__name__
        resource_type = self._resource_map.get(class_name)
        if not resource_type:
            raise TypeError(f"Unsupported record type: {class_name}")
        return resource_type

    def _build_payload(
        self,
        record: ExpenseRecord | IncomeRecord,
        operation: str,
    ) -> dict[str, Any]:
        """Build sync payload from configuration.
        
        Generic method that reads field definitions from config and constructs
        the appropriate payload structure for any resource/operation combination.
        
        Args:
            record: The record to sync
            operation: The operation name (e.g., "AddExpense", "UpdateIncome")
        
        Returns:
            Dictionary containing the payload fields
        """
        resource_type = self._get_resource_type(record)
        resource_config = self.config["resources"][resource_type]
        operation_config = resource_config["operations"][operation]
        
        payload = {}
        device = self._get_primary_device()
        entity_cache = {}  # Cache entity lookups
        
        for field_spec in operation_config["fields"]:
            field_name = field_spec["name"]
            field_type = field_spec["type"]
            
            if field_type == "constant":
                payload[field_name] = field_spec["value"]
            
            elif field_type == "operation":
                payload[field_name] = operation
            
            elif field_type == "primary_device_id":
                payload[field_name] = device.device_id
            
            elif field_type == "key_singular":
                payload[field_name] = record.key
            
            elif field_type == "key_array":
                payload[field_name] = [record.key]
            
            elif field_type == "field":
                source = field_spec["source"]
                value = self._get_field_value(record, source, entity_cache)
                
                # Apply format if specified
                if "format" in field_spec:
                    value = self._format_value(value, field_spec["format"])
                
                # Apply default if value is None/empty
                if value in (None, "") and "default" in field_spec:
                    value = field_spec["default"]
                
                payload[field_name] = value
            
            elif field_type == "entity_device_key":
                entity_name = field_spec["entity"]
                source_field = field_spec["source"]
                entity_value = getattr(record, source_field)
                entity_data = self._get_entity_device_cached(entity_name, entity_value, entity_cache)
                payload[field_name] = entity_data["device_key"]
            
            elif field_type == "entity_device_id":
                entity_name = field_spec["entity"]
                source_field = field_spec["source"]
                entity_value = getattr(record, source_field)
                entity_data = self._get_entity_device_cached(entity_name, entity_value, entity_cache)
                payload[field_name] = entity_data["device_id"]
        
        return payload

    def _get_field_value(
        self,
        record: ExpenseRecord | IncomeRecord,
        source: str,
        entity_cache: dict[str, dict],
    ) -> Any:
        """Get field value from record, handling special source types."""
        if source == "currency_amount_or_amount":
            return record.currency_amount or record.amount
        elif source == "currency_or_account_currency":
            if record.currency:
                return record.currency
            # Get account currency from entity cache
            account_data = self._get_entity_device_cached("Account", record.account, entity_cache)
            return account_data.get("currency", "")
        else:
            # Direct field access
            return getattr(record, source)

    def _format_value(self, value: Any, format_type: str) -> Any:
        """Format value according to configuration."""
        if format_type == "string":
            return str(value)
        elif format_type == "float":
            return float(value)
        elif format_type == "isoformat":
            return value.isoformat()
        return value

    def _get_entity_device_cached(
        self,
        entity: str,
        name: str,
        cache: dict[str, dict],
    ) -> dict[str, Any]:
        """Get entity device info with caching."""
        cache_key = f"{entity}:{name}"
        if cache_key not in cache:
            cache[cache_key] = self._get_entity_device(entity, name)
        return cache[cache_key]

    def create_sync_record(
        self,
        record: ExpenseRecord | IncomeRecord,
        operation: str | None = None,
    ) -> int:
        """Create a SyncUpdate entry for any resource operation.
        
        Unified configuration-driven method that handles all CRUD operations
        for all resource types. The payload structure is determined by sync-config.json.
        
        Args:
            record: The record to sync (ExpenseRecord, IncomeRecord, etc.)
            operation: Optional operation name (e.g., "UpdateExpense", "DeleteIncome").
                      If not provided, defaults to "Add{ResourceType}"
        
        Returns:
            The SyncUpdate key that was created
            
        Raises:
            TypeError: If record type is not supported
            
        Examples:
            # Add operations (operation inferred)
            manager.create_sync_record(expense_record)  # Creates AddExpense
            manager.create_sync_record(income_record)   # Creates AddIncome
            
            # Update operations (operation explicit)
            manager.create_sync_record(expense_record, "UpdateExpense")
            manager.create_sync_record(income_record, "UpdateIncome")
            
            # Delete operations (operation explicit)
            manager.create_sync_record(expense_record, "DeleteExpense")
            manager.create_sync_record(income_record, "DeleteIncome")
        """
        # Determine operation if not provided
        if operation is None:
            resource_type = self._get_resource_type(record)
            operation = f"Add{resource_type.capitalize()}"
        
        # Build payload from configuration
        payload = self._build_payload(record, operation)
        
        # Encode and insert
        encoded = self._encode_payload(payload, record, operation)
        cursor = self.connection.execute(
            "INSERT INTO SyncUpdate (updateType, uuid, payload) VALUES (?, ?, ?)",
            (UPDATE_TYPE_ANY, str(uuid.uuid4()), encoded),
        )
        return int(cursor.lastrowid)

    def create_updates_for_changes(
        self,
        record: ExpenseRecord | IncomeRecord,
        operation: str,
        changed_fields: dict[str, object],
    ) -> list[int]:
        """Create multiple SyncUpdate entries for a resource update operation.
        
        Each changed field generates its own SyncUpdate entry with the complete
        final record state. This matches native app behavior where each attribute
        change creates a separate sync event.
        
        Uses configuration-driven approach for all payload building.
        
        Args:
            record: The final record after all updates (ExpenseRecord, IncomeRecord, etc.)
            operation: The sync operation (e.g., "UpdateExpense", "UpdateIncome")
            changed_fields: Dict of field names that were updated (values are ignored)
        
        Returns:
            List of SyncUpdate keys that were created
        """
        sync_keys = []
        for _ in changed_fields:
            sync_key = self.create_sync_record(record, operation)
            sync_keys.append(sync_key)
        return sync_keys

    def _encode_payload(
        self,
        payload: dict,
        record: ExpenseRecord | IncomeRecord,
        operation: str,
    ) -> str:
        """Encode operation dictionary to HomeBudget SyncUpdate payload format.
        
        Uses configuration-driven compression settings from sync-config.json.
        
        HomeBudget uses a specific encoding format:
        1. JSON serialization with compact formatting (no spaces)
        2. Full zlib compression with header and checksum (NOT raw deflate)
        3. Pad to min_size with null bytes if configured
        4. URL-safe base64 encoding (- and _ instead of + and /)
        5. Strip trailing = padding characters
        
        Args:
            payload: Dictionary containing operation data
            record: The record being synced (used to lookup config)
            operation: The operation name (used to lookup config)
            
        Returns:
            Variable-length URL-safe base64 encoded string
        """
        # Get compression config
        resource_type = self._get_resource_type(record)
        operation_config = self.config["resources"][resource_type]["operations"][operation]
        compression_config = operation_config["compression"]
        
        # JSON serialize
        json_str = json.dumps(payload, separators=(",", ":"))
        
        # Compress with full zlib format
        compressed = zlib.compress(
            json_str.encode("utf-8"),
            level=ZLIB_COMPRESSION_LEVEL,
            wbits=ZLIB_WBITS,
        )
        
        # Pad if configured
        min_size = compression_config["min_size"]
        if compression_config["pad_if_smaller"] and len(compressed) < min_size:
            compressed = compressed + b"\x00" * (min_size - len(compressed))
        
        # URL-safe base64 encode and strip padding
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
        return encoded.rstrip("=")

    # Legacy methods for backward compatibility (call config-driven implementation)
    
    def create_expense_update(self, expense: ExpenseRecord, operation: str = "AddExpense") -> int:
        """Legacy method - delegates to create_sync_record."""
        return self.create_sync_record(expense, operation)

    def create_income_update(self, income: IncomeRecord, operation: str = "AddIncome") -> int:
        """Legacy method - delegates to create_sync_record."""
        return self.create_sync_record(income, operation)

    def _get_primary_device(self) -> DeviceInfoRecord:
        """Return the primary device details."""
        row = self.connection.execute(
            "SELECT key, deviceId FROM DeviceInfo WHERE isPrimary = ? AND isActive = ? "
            "ORDER BY key LIMIT 1",
            (FLAG_Y, FLAG_Y),
        ).fetchone()
        if row is None:
            raise RuntimeError("Primary device not found")
        return DeviceInfoRecord(key=row[0], device_id=row[1])

    def _get_entity_device(self, table: str, name: str) -> dict[str, object]:
        """Resolve device identifiers for a named entity."""
        if table == "Account":
            row = self.connection.execute(
                "SELECT key, deviceIdKey, deviceKey, currency FROM Account WHERE name = ?",
                (name,),
            ).fetchone()
            currency = row[3] if row is not None else ""
        else:
            row = self.connection.execute(
                f"SELECT key, deviceIdKey, deviceKey FROM {table} WHERE name = ?",
                (name,),
            ).fetchone()
            currency = ""
        if row is None:
            raise RuntimeError(f"{table} not found: {name}")
        device_id = ""
        if row[1] is not None:
            device_id = self._resolve_device_id(int(row[1]))
        return {
            "entity_key": row[0],
            "device_key": row[2] if row[2] is not None else row[0],
            "device_id": device_id,
            "currency": currency,
        }

    def _resolve_device_id(self, device_key: int) -> str:
        """Resolve a device id from its key."""
        row = self.connection.execute(
            "SELECT deviceId FROM DeviceInfo WHERE key = ?",
            (device_key,),
        ).fetchone()
        if row is None:
            return ""
        return row[0]
