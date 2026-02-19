from __future__ import annotations

import datetime as dt
from decimal import Decimal
import sqlite3

import pytest

from homebudget import DuplicateError, IncomeDTO
from homebudget.client import HomeBudgetClient
from homebudget.exceptions import NotFoundError
from tests.utils.assertions import assert_operation
from tests.utils.sync_payload import decode_sync_payload


def _get_connection(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _make_income() -> IncomeDTO:
    return IncomeDTO(
        date=dt.date(2026, 2, 16),
        name="Salary and Wages",
        amount=Decimal("2500.00"),
        account="TWH IB USD",
        notes="TDD Test Income",
    )


def _make_forex_income() -> IncomeDTO:
    """Create income with forex (different currency from account)."""
    return IncomeDTO(
        date=dt.date(2026, 2, 16),
        name="Freelance",
        amount=Decimal("1500.00"),
        account="TWH IB USD",
        currency="SGD",
        currency_amount=Decimal("2000.00"),
        notes="TDD Forex Income",
    )


@pytest.mark.sit
def test_add_income_basic(test_db_path) -> None:
    """Add income with required fields only."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_income(_make_income())

    assert saved.key is not None
    assert saved.amount == Decimal("2500.00")
    assert saved.name == "Salary and Wages"


@pytest.mark.sit
def test_add_income_creates_accounttrans(test_db_path) -> None:
    """Adding income creates AccountTrans entry with transType=income (2)."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_income(_make_income())

    with _get_connection(str(test_db_path)) as connection:
        row = connection.execute(
            "SELECT key FROM AccountTrans WHERE transType = 2 AND transKey = ?",
            (saved.key,),
        ).fetchone()

    assert row is not None


@pytest.mark.sit
def test_add_income_creates_syncupdate(sync_test_db_path) -> None:
    """Adding income creates SyncUpdate with valid AddIncome payload."""
    with HomeBudgetClient(db_path=sync_test_db_path) as client:
        saved = client.add_income(_make_income())

    with _get_connection(str(sync_test_db_path)) as connection:
        row = connection.execute(
            "SELECT payload FROM SyncUpdate ORDER BY key DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    payload = decode_sync_payload(row["payload"])
    assert_operation(payload, "AddIncome")
    assert payload["deviceKey"] == saved.key
    assert payload["name"] == "Salary and Wages"
    assert payload["amount"] == "2500.00"


@pytest.mark.sit
def test_add_income_forex(sync_test_db_path) -> None:
    """Adding income with forex currency creates correct payload."""
    with HomeBudgetClient(db_path=sync_test_db_path) as client:
        saved = client.add_income(_make_forex_income())

    with _get_connection(str(sync_test_db_path)) as connection:
        row = connection.execute(
            "SELECT payload FROM SyncUpdate ORDER BY key DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    payload = decode_sync_payload(row["payload"])
    assert payload["currency"] == "SGD"
    assert payload["amount"] == "1500.00"
    assert payload["currencyAmount"] == "2000.00"


@pytest.mark.sit
def test_add_duplicate_income_raises_error(test_db_path) -> None:
    """Adding duplicate income raises DuplicateError."""
    income = _make_income()
    with HomeBudgetClient(db_path=test_db_path) as client:
        client.add_income(income)
        with pytest.raises(DuplicateError):
            client.add_income(income)


@pytest.mark.sit
def test_get_income_by_key(test_db_path) -> None:
    """Get income by key returns correct IncomeRecord."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_income(_make_income())
        retrieved = client.get_income(saved.key)

    assert retrieved.key == saved.key
    assert retrieved.name == saved.name
    assert retrieved.amount == saved.amount


@pytest.mark.sit
def test_list_incomes_all(test_db_path) -> None:
    """List all incomes returns all income records."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved1 = client.add_income(_make_income())
        income2 = IncomeDTO(
            date=dt.date(2026, 2, 17),
            name="Bonus",
            amount=Decimal("500.00"),
            account="TWH IB USD",
        )
        saved2 = client.add_income(income2)

    with HomeBudgetClient(db_path=test_db_path) as client:
        all_incomes = client.list_incomes()

    assert len(all_incomes) >= 2
    keys = [i.key for i in all_incomes]
    assert saved1.key in keys
    assert saved2.key in keys


@pytest.mark.sit
def test_list_incomes_with_date_filter(test_db_path) -> None:
    """List incomes with date range filter returns filtered records."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        income1 = IncomeDTO(
            date=dt.date(2026, 2, 10),
            name="Early Income",
            amount=Decimal("1000.00"),
            account="TWH IB USD",
        )
        saved1 = client.add_income(income1)

        income2 = IncomeDTO(
            date=dt.date(2026, 2, 20),
            name="Late Income",
            amount=Decimal("2000.00"),
            account="TWH IB USD",
        )
        saved2 = client.add_income(income2)

    with HomeBudgetClient(db_path=test_db_path) as client:
        filtered = client.list_incomes(
            start_date=dt.date(2026, 2, 15),
            end_date=dt.date(2026, 2, 25),
        )

    keys = [i.key for i in filtered]
    assert saved1.key not in keys
    assert saved2.key in keys


@pytest.mark.sit
def test_update_income_amount(test_db_path) -> None:
    """Update income amount and verify change."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_income(_make_income())
        updated = client.update_income(saved.key, amount=Decimal("3000.00"))

    assert updated.key == saved.key
    assert updated.amount == Decimal("3000.00")
    assert updated.name == saved.name


@pytest.mark.sit
def test_update_income_notes(test_db_path) -> None:
    """Update income notes and verify change."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_income(_make_income())
        updated = client.update_income(saved.key, notes="Updated notes")

    assert updated.notes == "Updated notes"


@pytest.mark.sit
def test_update_income_currency(test_db_path) -> None:
    """Update income to add forex currency."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_income(_make_income())
        updated = client.update_income(
            saved.key,
            currency="SGD",
            currency_amount=Decimal("3125.00"),
            exchange_rate=Decimal("0.8"),
        )

    assert updated.currency == "SGD"
    assert updated.currency_amount == Decimal("3125.00")
    # Amount is calculated: 3125.00 * 0.8 = 2500.00 (matches original amount)
    assert updated.amount == Decimal("2500.00")


@pytest.mark.sit
def test_update_income_creates_syncupdate(sync_test_db_path) -> None:
    """Updating income creates SyncUpdate with UpdateIncome operation."""
    with HomeBudgetClient(db_path=sync_test_db_path) as client:
        saved = client.add_income(_make_income())
        client.update_income(saved.key, amount=Decimal("3000.00"))

    with _get_connection(str(sync_test_db_path)) as connection:
        row = connection.execute(
            "SELECT payload FROM SyncUpdate ORDER BY key DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    payload = decode_sync_payload(row["payload"])
    assert_operation(payload, "UpdateIncome")
    assert payload["deviceKey"] == saved.key
    assert float(payload["amount"]) == 3000.00


@pytest.mark.sit
def test_delete_income_removes_accounttrans(test_db_path) -> None:
    """Deleting income removes AccountTrans entry."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_income(_make_income())
        client.delete_income(saved.key)

    with _get_connection(str(test_db_path)) as connection:
        row = connection.execute(
            "SELECT key FROM AccountTrans WHERE transType = 2 AND transKey = ?",
            (saved.key,),
        ).fetchone()

    assert row is None


@pytest.mark.sit
def test_delete_income_removes_income_record(test_db_path) -> None:
    """Deleting income removes Income record."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_income(_make_income())
        client.delete_income(saved.key)

    with _get_connection(str(test_db_path)) as connection:
        row = connection.execute(
            "SELECT key FROM Income WHERE key = ?",
            (saved.key,),
        ).fetchone()

    assert row is None


@pytest.mark.sit
def test_delete_income_creates_syncupdate(sync_test_db_path) -> None:
    """Deleting income creates SyncUpdate with DeleteIncome operation."""
    with HomeBudgetClient(db_path=sync_test_db_path) as client:
        saved = client.add_income(_make_income())
        client.delete_income(saved.key)

    with _get_connection(str(sync_test_db_path)) as connection:
        row = connection.execute(
            "SELECT payload FROM SyncUpdate ORDER BY key DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    payload = decode_sync_payload(row["payload"])
    assert_operation(payload, "DeleteIncome")
    assert payload["deviceKey"] == saved.key


@pytest.mark.sit
def test_income_crud_workflow(test_db_path) -> None:
    """Complete CRUD workflow: create, read, update, delete."""
    with HomeBudgetClient(db_path=test_db_path) as client:
        # Create
        income = _make_income()
        saved = client.add_income(income)
        assert saved.key is not None

        # Read
        retrieved = client.get_income(saved.key)
        assert retrieved.name == income.name
        assert retrieved.amount == income.amount

        # Update
        updated = client.update_income(saved.key, amount=Decimal("3500.00"))
        assert updated.amount == Decimal("3500.00")

        # Delete
        client.delete_income(saved.key)

        # Verify deleted
        with pytest.raises(NotFoundError):
            client.get_income(saved.key)
