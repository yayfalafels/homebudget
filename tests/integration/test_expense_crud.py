from __future__ import annotations

import datetime as dt
from decimal import Decimal
import sqlite3

import pytest

from homebudget import DuplicateError, ExpenseDTO
from homebudget.client import HomeBudgetClient
from tests.utils.assertions import assert_operation
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
        notes="TDD Test Expense",
    )


@pytest.mark.sit
def test_add_expense_basic(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_expense(_make_expense())

    assert saved.key is not None
    assert saved.amount == Decimal("25.50")


@pytest.mark.sit
def test_add_expense_creates_accounttrans(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_expense(_make_expense())

    with _get_connection(str(test_db_path)) as connection:
        row = connection.execute(
            "SELECT key FROM AccountTrans WHERE transType = 1 AND transKey = ?",
            (saved.key,),
        ).fetchone()

    assert row is not None


@pytest.mark.sit
def test_add_expense_creates_syncupdate(sync_test_db_path) -> None:
    with HomeBudgetClient(db_path=sync_test_db_path) as client:
        saved = client.add_expense(_make_expense())

    with _get_connection(str(sync_test_db_path)) as connection:
        row = connection.execute(
            "SELECT payload FROM SyncUpdate ORDER BY key DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    payload = decode_sync_payload(row["payload"])
    assert_operation(payload, "AddExpense")
    assert saved.key in payload["expenseDeviceKeys"]


@pytest.mark.sit
def test_add_duplicate_expense_raises_error(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        client.add_expense(_make_expense())
        with pytest.raises(DuplicateError):
            client.add_expense(_make_expense())


@pytest.mark.sit
def test_get_expense_by_key(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_expense(_make_expense())
        fetched = client.get_expense(saved.key)

    assert fetched.key == saved.key
    assert fetched.amount == saved.amount


@pytest.mark.sit
def test_list_expenses_with_filters(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        client.add_expense(_make_expense())
        results = client.list_expenses(
            start_date=dt.date(2026, 2, 1),
            end_date=dt.date(2026, 2, 28),
        )

    assert results
    assert any(expense.amount == Decimal("25.50") for expense in results)


@pytest.mark.sit
def test_update_expense_amount(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_expense(_make_expense())
        updated = client.update_expense(saved.key, amount=Decimal("27.50"))

    assert updated.amount == Decimal("27.50")


@pytest.mark.sit
def test_delete_expense_removes_accounttrans(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_expense(_make_expense())
        client.delete_expense(saved.key)

    with _get_connection(str(test_db_path)) as connection:
        expense_row = connection.execute(
            "SELECT key FROM Expense WHERE key = ?",
            (saved.key,),
        ).fetchone()
        acc_row = connection.execute(
            "SELECT key FROM AccountTrans WHERE transType = 1 AND transKey = ?",
            (saved.key,),
        ).fetchone()

    assert expense_row is None
    assert acc_row is None
