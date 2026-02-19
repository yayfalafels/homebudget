from __future__ import annotations

import datetime as dt
from decimal import Decimal
import sqlite3

import pytest

from homebudget import DuplicateError, TransferDTO
from homebudget.client import HomeBudgetClient
from tests.utils.assertions import assert_operation
from tests.utils.sync_payload import decode_sync_payload


def _get_connection(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _make_transfer() -> TransferDTO:
    return TransferDTO(
        date=dt.date(2026, 2, 20),
        from_account="Bank TWH SGD",
        to_account="Wallet",
        amount=Decimal("200.00"),
        notes="TDD Test Transfer",
    )


@pytest.mark.sit
def test_add_transfer_basic(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_transfer(_make_transfer())

    assert saved.key is not None
    assert saved.amount == Decimal("200.00")


@pytest.mark.sit
def test_add_transfer_creates_dual_accounttrans(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_transfer(_make_transfer())

    with _get_connection(str(test_db_path)) as connection:
        # Check transfer_out entry
        out_row = connection.execute(
            "SELECT key FROM AccountTrans WHERE transType = 3 AND transKey = ?",
            (saved.key,),
        ).fetchone()
        # Check transfer_in entry
        in_row = connection.execute(
            "SELECT key FROM AccountTrans WHERE transType = 4 AND transKey = ?",
            (saved.key,),
        ).fetchone()

    assert out_row is not None
    assert in_row is not None


@pytest.mark.sit
def test_add_transfer_creates_syncupdate(sync_test_db_path) -> None:
    with HomeBudgetClient(db_path=sync_test_db_path) as client:
        saved = client.add_transfer(_make_transfer())

    with _get_connection(str(sync_test_db_path)) as connection:
        row = connection.execute(
            "SELECT payload FROM SyncUpdate ORDER BY key DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    payload = decode_sync_payload(row["payload"])
    assert_operation(payload, "AddTransfer")
    assert saved.key in payload["transferDeviceKeys"]


@pytest.mark.sit
def test_add_duplicate_transfer_raises_error(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        client.add_transfer(_make_transfer())
        with pytest.raises(DuplicateError):
            client.add_transfer(_make_transfer())


@pytest.mark.sit
def test_get_transfer_by_key(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_transfer(_make_transfer())
        fetched = client.get_transfer(saved.key)

    assert fetched.key == saved.key
    assert fetched.amount == saved.amount


@pytest.mark.sit
def test_list_transfers_with_filters(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        client.add_transfer(_make_transfer())
        results = client.list_transfers(
            start_date=dt.date(2026, 2, 1),
            end_date=dt.date(2026, 2, 28),
        )

    assert results
    assert any(transfer.amount == Decimal("200.00") for transfer in results)


@pytest.mark.sit
def test_update_transfer_amount(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_transfer(_make_transfer())
        updated = client.update_transfer(saved.key, amount=Decimal("250.00"))

    assert updated.amount == Decimal("250.00")


@pytest.mark.sit
def test_delete_transfer_removes_dual_accounttrans(test_db_path) -> None:
    with HomeBudgetClient(db_path=test_db_path) as client:
        saved = client.add_transfer(_make_transfer())
        client.delete_transfer(saved.key)

    with _get_connection(str(test_db_path)) as connection:
        transfer_row = connection.execute(
            "SELECT key FROM Transfer WHERE key = ?",
            (saved.key,),
        ).fetchone()
        out_row = connection.execute(
            "SELECT key FROM AccountTrans WHERE transType = 3 AND transKey = ?",
            (saved.key,),
        ).fetchone()
        in_row = connection.execute(
            "SELECT key FROM AccountTrans WHERE transType = 4 AND transKey = ?",
            (saved.key,),
        ).fetchone()

    assert transfer_row is None
    assert out_row is None
    assert in_row is None
