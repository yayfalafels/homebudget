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
MIN_PAYLOAD_PAD_LENGTH = 512  # Minimum payload size before base64 encoding (683 chars after)


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
          * Uses singular expenseDeviceKey field
          * Compressed then padded to 512 bytes minimum
          * Results in 683-char base64 string
        
        - AddExpense: Full 22-field payload with complete details
          * Uses plural expenseDeviceKeys array
          * Compressed size ~689 bytes (no padding needed)
          * Results in 919-920 char base64 string
        
        - UpdateExpense: 18-field payload with updated details
          * Uses singular expenseDeviceKey field (not plural like Add)
          * Compressed size ~624 bytes (no padding needed)
          * Results in 832-834 char base64 string
        
        Inspection findings (2026-02-17): Payload sizes vary by operation and content.
        Income/Transfer operations pad to 512 bytes minimum. Expense operations don't
        need padding as they compress to >512 bytes due to more fields.
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
        elif operation == "AddExpense":
            # AddExpense uses full payload with plural expenseDeviceKeys array
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
        else:
            # UpdateExpense uses singular expenseDeviceKey (not plural like Add)
            device = self._get_primary_device()
            account_device = self._get_entity_device("Account", expense.account)
            category_device = self._get_entity_device("Category", expense.category)
            subcategory_device = self._get_entity_device("SubCategory", expense.subcategory)

            payload = {
                "Operation": operation,
                "accountDeviceKey": account_device["device_key"],
                "timeStamp": expense.time_stamp,
                "expenseDeviceKey": expense.key,  # Singular for UpdateExpense
                "currencyAmount": str(expense.currency_amount or expense.amount),
                "expenseDateString": expense.date.isoformat(),
                "receiptImageNeedsSaving": "False",
                "currency": expense.currency or account_device["currency"],
                "categoryDeviceKey": category_device["device_key"],
                "amount": float(expense.amount),
                "accountDeviceId": account_device["device_id"],
                "notesString": expense.notes or "",
                "payeeDeviceKey": 0,
                "payeeDeviceId": "",
                "subcategoryDeviceId": subcategory_device["device_id"],
                "subcategoryDeviceKey": subcategory_device["device_key"],
                "deviceId": device.device_id,
                "categoryDeviceId": category_device["device_id"],
            }

        encoded = self.encode_payload(payload)
        # Based on inspection of UI-generated SyncUpdate entries (2026-02-17):
        # updateType is ALWAYS "Any" regardless of operation type.
        # The actual operation is specified in the payload's "Operation" field.
        cursor = self.connection.execute(
            "INSERT INTO SyncUpdate (updateType, uuid, payload) VALUES (?, ?, ?)",
            ("Any", str(uuid.uuid4()), encoded),
        )
        return int(cursor.lastrowid)

    def encode_payload(self, operation: dict) -> str:
        """Encode operation dictionary to HomeBudget SyncUpdate payload format.
        
        HomeBudget uses a specific encoding format that must be matched exactly:
        1. JSON serialization with compact formatting (no spaces)
        2. Full zlib compression with header and checksum (NOT raw deflate)
        3. Pad to 512 bytes minimum with null bytes if needed
        4. URL-safe base64 encoding (- and _ instead of + and /)
        5. Strip trailing = padding characters
        
        Inspection findings (2026-02-17): Payload sizes vary by operation:
        - Delete/Income/Transfer operations: Pad to 512 bytes → 683 chars base64
        - Expense Add operations: ~689 bytes compressed → 919-920 chars base64
        - Expense Update operations: ~624 bytes compressed → 832-834 chars base64
        
        Args:
            operation: Dictionary containing operation data (e.g., AddExpense payload)
            
        Returns:
            Variable-length URL-safe base64 encoded string (683-920 chars typical)
        """
        json_str = json.dumps(operation, separators=(",", ":"))
        # Use full zlib compression with header and checksum
        # Inverse of zlib.decompress(data, wbits=ZLIB_WBITS)
        compressed = zlib.compress(
            json_str.encode("utf-8"), 
            level=ZLIB_COMPRESSION_LEVEL, 
            wbits=ZLIB_WBITS
        )
        
        # Pad with null bytes to minimum size if needed
        # Smaller payloads (Delete/Income/Transfer) are padded to 512 bytes
        # Larger payloads (Expense Add/Update) don't need padding
        if len(compressed) < MIN_PAYLOAD_PAD_LENGTH:
            compressed = compressed + b'\x00' * (MIN_PAYLOAD_PAD_LENGTH - len(compressed))
        
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
