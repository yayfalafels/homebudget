from __future__ import annotations

from dataclasses import dataclass
import base64
import json
from decimal import Decimal
import sqlite3
import uuid
import zlib

from homebudget.models import ExpenseRecord


@dataclass(frozen=True)
class DeviceInfoRecord:
    key: int
    device_id: str


class SyncUpdateManager:
    def __init__(self, connection: sqlite3.Connection | None) -> None:
        if connection is None:
            raise RuntimeError("Connection is required for sync updates")
        self.connection = connection

    def create_expense_update(self, expense: ExpenseRecord) -> int:
        device = self._get_primary_device()
        account_device = self._get_entity_device("Account", expense.account)
        category_device = self._get_entity_device("Category", expense.category)
        subcategory_device = self._get_entity_device("SubCategory", expense.subcategory)

        payload = {
            "periods": 1,
            "Operation": "AddExpense",
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
            ("Any", str(uuid.uuid4()), encoded),
        )
        return int(cursor.lastrowid)

    def encode_payload(self, operation: dict) -> str:
        json_str = json.dumps(operation, separators=(",", ":"))
        compressed = zlib.compress(json_str.encode("utf-8"), level=9)
        raw_deflate = compressed[2:-4]
        encoded = base64.b64encode(raw_deflate).decode("ascii")
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
