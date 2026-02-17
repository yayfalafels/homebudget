from __future__ import annotations

from dataclasses import dataclass
import base64
import json
from decimal import Decimal
import sqlite3
import uuid
import zlib

from homebudget.models import ExpenseRecord

# SyncUpdate payload encoding constants
ZLIB_COMPRESSION_LEVEL = 9  # Maximum compression
ZLIB_WBITS = 15  # Full zlib format with header and checksum
PAYLOAD_PAD_LENGTH = 660  # Fixed payload size before base64 encoding
PAYLOAD_BASE64_LENGTH = 880  # Fixed base64 string length after encoding


@dataclass(frozen=True)
class DeviceInfoRecord:
    key: int
    device_id: str


class SyncUpdateManager:
    def __init__(self, connection: sqlite3.Connection | None) -> None:
        if connection is None:
            raise RuntimeError("Connection is required for sync updates")
        self.connection = connection

    def create_expense_update(
        self,
        expense: ExpenseRecord,
        operation: str = "AddExpense",
    ) -> int:
        """Create a SyncUpdate entry for an expense operation.
        
        CRITICAL: Delete vs Add/Update operations use completely different payload
        structures. This mismatch was the root cause of Issue 002.
        
        - DeleteExpense: Minimal 3-field payload (Operation, expenseDeviceKey, deviceId)
          * Compressed size: ~512 bytes
          * Base64 length: ~683 chars
          * Mobile app deletes record by key, doesn't need transaction details
        
        - AddExpense/UpdateExpense: Full 20+ field payload with complete details
          * Compressed size: 660 bytes (fixed)
          * Base64 length: 880 chars (fixed)
          * Mobile app inserts/updates record, needs all transaction information
        
        Using wrong structure causes mobile sync to fail or ignore the operation.
        """
        # Delete operations have a completely different payload structure
        # They only need Operation, expenseDeviceKey (singular), and deviceId
        if operation == "DeleteExpense":
            device = self._get_primary_device()
            payload = {
                "Operation": operation,
                "expenseDeviceKey": expense.key,
                "deviceId": device.device_id,
            }
        else:
            # AddExpense and UpdateExpense use full payload with complete expense details
            device = self._get_primary_device()
            account_device = self._get_entity_device("Account", expense.account)
            category_device = self._get_entity_device("Category", expense.category)
            subcategory_device = self._get_entity_device("SubCategory", expense.subcategory)

            payload = {
                "periods": 1,
                "Operation": operation,
                "accountDeviceKey": account_device["device_key"],
                "timeStamp": expense.time_stamp,
                "expenseDeviceKeys": [expense.key],
                "currencyAmount": str(expense.currency_amount or expense.amount),
                "billDeviceKey": 0,
                "billDeviceId": "",
                "expenseDateString": expense.date.isoformat(),
                "receiptImageNeedsSaving": "False",
                "currency": expense.currency or account_device["currency"],
                "categoryDeviceKey": category_device["device_key"],
                "amount": float(expense.amount),
                "accountDeviceId": account_device["device_id"],
                "notesString": expense.notes or "",
                "payeeDeviceKey": 0,
                "payeeDeviceId": "",
                "recurringKey": 0,
                "subcategoryDeviceId": subcategory_device["device_id"],
                "subcategoryDeviceKey": subcategory_device["device_key"],
                "deviceId": device.device_id,
                "categoryDeviceId": category_device["device_id"],
            }

        encoded = self.encode_payload(payload)
        cursor = self.connection.execute(
            "INSERT INTO SyncUpdate (updateType, uuid, payload) VALUES (?, ?, ?)",
            (operation, str(uuid.uuid4()), encoded),
        )
        return int(cursor.lastrowid)

    def encode_payload(self, operation: dict) -> str:
        """Encode operation dictionary to HomeBudget SyncUpdate payload format.
        
        HomeBudget uses a specific encoding format that must be matched exactly:
        1. JSON serialization with compact formatting (no spaces)
        2. Full zlib compression with header and checksum (NOT raw deflate)
        3. Padding to fixed 660-byte length with null bytes
        4. URL-safe base64 encoding (- and _ instead of + and /)
        5. Strip trailing = padding characters
        
        The result is always an 880-character string.
        
        Critical discovery (2026-02-17): Native app uses zlib.compress() directly
        without stripping header/checksum. Earlier implementations incorrectly
        assumed raw deflate format and stripped bytes [2:-4], causing sync failures.
        
        Args:
            operation: Dictionary containing operation data (e.g., AddExpense payload)
            
        Returns:
            880-character URL-safe base64 encoded string
        """
        json_str = json.dumps(operation, separators=(",", ":"))
        # Use full zlib compression with header and checksum
        # Inverse of zlib.decompress(data, wbits=ZLIB_WBITS)
        compressed = zlib.compress(
            json_str.encode("utf-8"), 
            level=ZLIB_COMPRESSION_LEVEL, 
            wbits=ZLIB_WBITS
        )
        
        # Pad with null bytes to match HomeBudget's fixed-size format
        # PAYLOAD_PAD_LENGTH bytes → PAYLOAD_BASE64_LENGTH chars after encoding
        if len(compressed) < PAYLOAD_PAD_LENGTH:
            compressed = compressed + b'\x00' * (PAYLOAD_PAD_LENGTH - len(compressed))
        
        # Use URL-safe base64 encoding (matches native app)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
        return encoded.rstrip("=")

    def _get_primary_device(self) -> DeviceInfoRecord:
        row = self.connection.execute(
            "SELECT key, deviceId FROM DeviceInfo WHERE isPrimary = 'Y' AND isActive = 'Y' "
            "ORDER BY key LIMIT 1"
        ).fetchone()
        if row is None:
            raise RuntimeError("Primary device not found")
        return DeviceInfoRecord(key=row[0], device_id=row[1])

    def _get_entity_device(self, table: str, name: str) -> dict[str, object]:
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
        row = self.connection.execute(
            "SELECT deviceId FROM DeviceInfo WHERE key = ?",
            (device_key,),
        ).fetchone()
        if row is None:
            return ""
        return row[0]
