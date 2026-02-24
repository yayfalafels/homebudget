"""Integration tests for CLI balance command."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
import sqlite3

import pytest
from click.testing import CliRunner

from homebudget.cli.main import main
from homebudget.schema import TRANSACTION_TYPES


def _get_connection(db_path: str) -> sqlite3.Connection:
    """Create a database connection for test setup."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _setup_cli_test_data(db_path: str) -> None:
    """Set up test data for CLI balance command."""
    with _get_connection(db_path) as conn:
        # Get TWH IB USD account
        account_row = conn.execute(
            "SELECT key FROM Account WHERE name = 'TWH IB USD' LIMIT 1"
        ).fetchone()
        account_key = account_row["key"]
        
        # Clear existing transactions in January 2026
        conn.execute(
            "DELETE FROM AccountTrans WHERE accountKey = ? AND transDate >= '2026-01-01' AND transDate < '2026-02-01'",
            (account_key,)
        )
        
        # Insert reconcile balance on 2026-01-15: 1000.00
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
                0,
                "2026-01-15",
                1000.00,
                "N",
            ),
        )
        
        # Insert transaction after reconcile: +200.00
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
        
        conn.commit()


@pytest.mark.sit
def test_cli_balance_command_with_account(test_db_path) -> None:
    """Test balance command with account parameter."""
    _setup_cli_test_data(str(test_db_path))
    
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--db", str(test_db_path), "account", "balance", "--account", "TWH IB USD"],
    )
    
    assert result.exit_code == 0
    assert "Account Balance: TWH IB USD" in result.output
    assert "Balance:" in result.output


@pytest.mark.sit
def test_cli_balance_command_with_date(test_db_path) -> None:
    """Test balance command with explicit date parameter."""
    _setup_cli_test_data(str(test_db_path))
    
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--db",
            str(test_db_path),
            "account",
            "balance",
            "--account",
            "TWH IB USD",
            "--date",
            "2026-01-25",
        ],
    )
    
    assert result.exit_code == 0
    assert "Account Balance: TWH IB USD" in result.output
    assert "Query Date: 2026-01-25" in result.output
    assert "Balance: 1200.00" in result.output


@pytest.mark.sit
def test_cli_balance_command_output_format(test_db_path) -> None:
    """Test balance command output contains all required information."""
    _setup_cli_test_data(str(test_db_path))
    
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--db", str(test_db_path), "account", "balance", "--account", "TWH IB USD"],
    )
    
    assert result.exit_code == 0
    assert "Account Balance:" in result.output
    assert "Query Date:" in result.output
    assert "Balance:" in result.output
    assert "Reconcile Date:" in result.output
    assert "Reconcile Amount:" in result.output
