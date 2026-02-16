from __future__ import annotations

import datetime as dt
from decimal import Decimal
import sqlite3

import pytest

from homebudget import ExpenseDTO
from homebudget.client import HomeBudgetClient
from tests.utils.assertions import assert_operation, assert_required_keys
from tests.utils.sync_payload import decode_sync_payload


def _get_connection(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _make_expense() -> ExpenseDTO:
    return ExpenseDTO(
        date=dt.date(2026, 2, 16),
        category="Food (Basic)",
        subcategory="Groceries",
        amount=Decimal("25.50"),
        account="Cash TWH SGD",
        notes="Sync validation",
    )


@pytest.mark.sit
def test_sync_payload_add_expense(sync_test_db_path) -> None:
    with HomeBudgetClient(db_path=sync_test_db_path) as client:
        saved = client.add_expense(_make_expense())

    with _get_connection(str(sync_test_db_path)) as connection:
        row = connection.execute(
            "SELECT payload FROM SyncUpdate ORDER BY key DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    payload = decode_sync_payload(row["payload"])

    assert_operation(payload, "AddExpense")
    assert_required_keys(
        payload,
        [
            "Operation",
            "expenseDeviceKeys",
            "deviceId",
            "timeStamp",
            "expenseDateString",
            "accountDeviceKey",
            "accountDeviceId",
            "categoryDeviceKey",
            "categoryDeviceId",
            "subcategoryDeviceKey",
            "subcategoryDeviceId",
            "amount",
            "currency",
            "currencyAmount",
            "notesString",
        ],
    )

    assert saved.key in payload["expenseDeviceKeys"]
