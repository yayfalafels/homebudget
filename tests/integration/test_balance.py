"""Integration tests for account balance calculations."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
import sqlite3

import pytest

from homebudget.client import HomeBudgetClient
from homebudget.exceptions import NotFoundError
from homebudget.models import BalanceRecord
from homebudget.repository import Repository
from homebudget.schema import TRANSACTION_TYPES


def _get_connection(db_path: str) -> sqlite3.Connection:
    """Create a database connection for test setup."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _setup_balance_test_data(db_path: str) -> tuple[int, dt.date]:
    """Set up test data with reconcile balance and transactions.
    
    Returns:
        Tuple of (account_key, reconcile_date)
    """
    with _get_connection(db_path) as conn:
        # Get an existing account
        account_row = conn.execute(
            "SELECT key FROM Account WHERE name = 'TWH IB USD' LIMIT 1"
        ).fetchone()
        account_key = account_row["key"]
        
        # Clear any existing AccountTrans records for this account in 2026-01
        conn.execute(
            "DELETE FROM AccountTrans WHERE accountKey = ? AND transDate >= '2026-01-01' AND transDate < '2026-02-01'",
            (account_key,)
        )
        
        # Set reconcile date to 2026-01-15
        reconcile_date = dt.date(2026, 1, 15)
        reconcile_amount = Decimal("1000.00")
        
        # Insert reconcile balance (transType=0) into AccountTrans
        conn.execute(
            """
            INSERT INTO AccountTrans (
                accountKey, timeStamp, transType, transKey, transDate, transAmount, checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_key,
                dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                TRANSACTION_TYPES["balance"],
                0,  # transKey for balance records
                reconcile_date.isoformat(),
                float(reconcile_amount),
                "N",
            ),
        )
        
        # Insert transaction before reconcile date, between query and reconcile (2026-01-14): +50.00
        # This will be used to test backward calculation
        conn.execute(
            """
            INSERT INTO AccountTrans (
                accountKey, timeStamp, transType, transKey, transDate, transAmount, checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_key,
                dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                TRANSACTION_TYPES["income"],
                999,
                "2026-01-14",
                50.00,
                "N",
            ),
        )
        
        # Insert transaction after reconcile date (2026-01-20): +200.00
        conn.execute(
            """
            INSERT INTO AccountTrans (
                accountKey, timeStamp, transType, transKey, transDate, transAmount, checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_key,
                dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                TRANSACTION_TYPES["income"],
                998,
                "2026-01-20",
                200.00,
                "N",
            ),
        )
        
        # Insert transaction after reconcile date (2026-01-25): 75.00 expense
        conn.execute(
            """
            INSERT INTO AccountTrans (
                accountKey, timeStamp, transType, transKey, transDate, transAmount, checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_key,
                dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                TRANSACTION_TYPES["expense"],
                997,
                "2026-01-25",
                75.00,
                "N",
            ),
        )
        
        conn.commit()
    
    return account_key, reconcile_date


@pytest.mark.sit
def test_balance_after_reconcile_date(test_db_path) -> None:
    """Query balance after reconcile date should sum forward from reconcile."""
    account_key, reconcile_date = _setup_balance_test_data(str(test_db_path))
    
    repo = Repository(test_db_path)
    repo.connect()
    
    try:
        # Query date: 2026-01-30 (after all transactions)
        # Expected: reconcile (1000) + 200 - 75 = 1125
        query_date = dt.date(2026, 1, 30)
        result = repo.get_account_balance(account_key, query_date)
        
        assert result["accountKey"] == account_key
        assert result["queryDate"] == query_date
        assert result["balanceAmount"] == Decimal("1125.00")
        assert result["reconcileDate"] == reconcile_date
        assert result["reconcileAmount"] == Decimal("1000.00")
    finally:
        repo.close()


@pytest.mark.sit
def test_balance_before_reconcile_date(test_db_path) -> None:
    """Query balance before reconcile date should sum backward from reconcile."""
    account_key, reconcile_date = _setup_balance_test_data(str(test_db_path))
    
    repo = Repository(test_db_path)
    repo.connect()
    
    try:
        # Query date: 2026-01-12 (before reconcile)
        # Transaction on 01-14 (+50) is between query and reconcile
        # Expected: reconcile (1000) - 50 = 950
        query_date = dt.date(2026, 1, 12)
        result = repo.get_account_balance(account_key, query_date)
        
        assert result["accountKey"] == account_key
        assert result["queryDate"] == query_date
        assert result["balanceAmount"] == Decimal("950.00")
        assert result["reconcileDate"] == reconcile_date
        assert result["reconcileAmount"] == Decimal("1000.00")
    finally:
        repo.close()


@pytest.mark.sit
def test_balance_on_reconcile_date(test_db_path) -> None:
    """Query balance on exact reconcile date should return reconcile amount only."""
    account_key, reconcile_date = _setup_balance_test_data(str(test_db_path))
    
    repo = Repository(test_db_path)
    repo.connect()
    
    try:
        # Query date: 2026-01-15 (exact reconcile date)
        # Expected: reconcile amount only (1000)
        query_date = reconcile_date
        result = repo.get_account_balance(account_key, query_date)
        
        assert result["accountKey"] == account_key
        assert result["queryDate"] == query_date
        assert result["balanceAmount"] == Decimal("1000.00")
        assert result["reconcileDate"] == reconcile_date
        assert result["reconcileAmount"] == Decimal("1000.00")
    finally:
        repo.close()


@pytest.mark.sit
def test_missing_reconcile_balance_raises_error(test_db_path) -> None:
    """Account without reconcile balance should raise NotFoundError."""
    with _get_connection(str(test_db_path)) as conn:
        # Get an account and ensure it has no reconcile balance
        account_row = conn.execute(
            "SELECT key FROM Account LIMIT 1"
        ).fetchone()
        account_key = account_row["key"]
        # Delete any existing balance records
        conn.execute(
            "DELETE FROM AccountTrans WHERE accountKey = ? AND transType = ?",
            (account_key, TRANSACTION_TYPES["balance"])
        )
        conn.commit()
    
    repo = Repository(test_db_path)
    repo.connect()
    
    try:
        query_date = dt.date(2026, 1, 15)
        with pytest.raises(NotFoundError, match="Reconcile balance not found"):
            repo.get_account_balance(account_key, query_date)
    finally:
        repo.close()


@pytest.mark.sit
def test_client_get_balance_with_account_name(test_db_path) -> None:
    """Client should resolve account name to key and return BalanceRecord."""
    _setup_balance_test_data(str(test_db_path))
    
    with HomeBudgetClient(db_path=test_db_path) as client:
        query_date = dt.date(2026, 1, 30)
        result = client.get_account_balance("TWH IB USD", query_date)
        
        assert isinstance(result, BalanceRecord)
        assert result.accountName == "TWH IB USD"
        assert result.queryDate == query_date
        assert result.balanceAmount == Decimal("1125.00")
        assert result.reconcileAmount == Decimal("1000.00")


@pytest.mark.sit
def test_client_balance_uses_today_by_default(test_db_path) -> None:
    """Client should default query_date to today when None."""
    _setup_balance_test_data(str(test_db_path))
    
    with HomeBudgetClient(db_path=test_db_path) as client:
        result = client.get_account_balance("TWH IB USD")
        
        assert isinstance(result, BalanceRecord)
        assert result.queryDate == dt.date.today()


@pytest.mark.sit
def test_client_balance_with_explicit_date(test_db_path) -> None:
    """Client should accept explicit query_date parameter."""
    _setup_balance_test_data(str(test_db_path))
    
    with HomeBudgetClient(db_path=test_db_path) as client:
        query_date = dt.date(2026, 1, 12)
        result = client.get_account_balance("TWH IB USD", query_date)
        
        assert isinstance(result, BalanceRecord)
        assert result.queryDate == query_date
        assert result.balanceAmount == Decimal("950.00")
