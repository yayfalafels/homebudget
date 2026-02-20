"""Integration tests for batch operations."""

from __future__ import annotations

import csv
import datetime as dt
import json
from decimal import Decimal
from pathlib import Path
import pytest
import shutil
import sqlite3

from homebudget import HomeBudgetClient
from homebudget.models import ExpenseDTO, IncomeDTO, TransferDTO


@pytest.fixture
def batch_test_db(tmp_path: Path) -> Path:
    """Create a temporary test database for batch operations."""
    source = Path("tests/fixtures/test_database.db")
    dest = tmp_path / "batch_test.db"
    shutil.copy(source, dest)
    return dest


@pytest.fixture
def batch_expenses_csv() -> Path:
    """Path to batch expenses CSV file."""
    return Path("tests/fixtures/batch_expenses.csv")


@pytest.fixture
def batch_income_json() -> Path:
    """Path to batch income JSON file."""
    return Path("tests/fixtures/batch_income.json")


@pytest.fixture
def batch_transfers_csv() -> Path:
    """Path to batch transfers CSV file."""
    return Path("tests/fixtures/batch_transfers.csv")


@pytest.fixture
def batch_expenses_with_errors_csv() -> Path:
    """Path to batch expenses CSV with errors."""
    return Path("tests/fixtures/batch_expenses_with_errors.csv")


class TestBatchExpenseOperations:
    """Test batch expense operations."""

    def test_add_expenses_batch_from_dtos(self, batch_test_db: Path) -> None:
        """Batch add expenses from DTO list."""
        expenses = [
            ExpenseDTO(
                date=dt.date(2026, 2, 1),
                category="Food (Basic)",
                subcategory="Groceries",
                amount=Decimal("45.50"),
                account="TWH - Personal",
                notes="Batch expense 1",
            ),
            ExpenseDTO(
                date=dt.date(2026, 2, 2),
                category="Transport",
                subcategory="Gas",
                amount=Decimal("60.00"),
                account="TWH - Personal",
                notes="Batch expense 2",
            ),
            ExpenseDTO(
                date=dt.date(2026, 2, 3),
                category="Food (Basic)",
                subcategory="Cheap restaurant",
                amount=Decimal("15.75"),
                account="TWH - Personal",
                notes="Batch expense 3",
            ),
        ]

        with HomeBudgetClient(db_path=batch_test_db, enable_sync=False) as client:
            result = client.add_expenses_batch(expenses)

        assert len(result.successful) == 3
        assert len(result.failed) == 0
        assert all(record.key > 0 for record in result.successful)

    def test_add_expenses_batch_with_errors(self, batch_test_db: Path) -> None:
        """Batch add with some invalid expenses continues and reports errors."""
        expenses = [
            ExpenseDTO(
                date=dt.date(2026, 2, 1),
                category="Food (Basic)",
                subcategory="Groceries",
                amount=Decimal("45.50"),
                account="TWH - Personal",
                notes="Valid expense",
            ),
            ExpenseDTO(
                date=dt.date(2026, 2, 2),
                category="InvalidCategory",
                subcategory="Groceries",
                amount=Decimal("60.00"),
                account="TWH - Personal",
                notes="Invalid category",
            ),
            ExpenseDTO(
                date=dt.date(2026, 2, 3),
                category="Food (Basic)",
                subcategory="Cheap restaurant",
                amount=Decimal("15.75"),
                account="TWH - Personal",
                notes="Valid expense",
            ),
        ]

        with HomeBudgetClient(db_path=batch_test_db, enable_sync=False) as client:
            result = client.add_expenses_batch(expenses, continue_on_error=True)

        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert result.failed[0][0].category == "InvalidCategory"

    def test_add_expenses_batch_stop_on_error(self, batch_test_db: Path) -> None:
        """Batch add stops on first error when continue_on_error is False."""
        expenses = [
            ExpenseDTO(
                date=dt.date(2026, 2, 1),
                category="Food (Basic)",
                subcategory="Groceries",
                amount=Decimal("45.50"),
                account="TWH - Personal",
                notes="Valid expense",
            ),
            ExpenseDTO(
                date=dt.date(2026, 2, 2),
                category="InvalidCategory",
                subcategory="Groceries",
                amount=Decimal("60.00"),
                account="TWH - Personal",
                notes="Invalid category",
            ),
            ExpenseDTO(
                date=dt.date(2026, 2, 3),
                category="Food (Basic)",
                subcategory="Cheap restaurant",
                amount=Decimal("15.75"),
                account="TWH - Personal",
                notes="Should not process",
            ),
        ]

        with HomeBudgetClient(db_path=batch_test_db, enable_sync=False) as client:
            with pytest.raises(Exception):  # Should raise on first error
                client.add_expenses_batch(expenses, continue_on_error=False)

    def test_add_expenses_batch_creates_sync_after_batch(self, batch_test_db: Path) -> None:
        """Batch add creates a single sync entry after all inserts."""
        expenses = [
            ExpenseDTO(
                date=dt.date(2026, 2, 1),
                category="Food (Basic)",
                subcategory="Groceries",
                amount=Decimal("45.50"),
                account="TWH - Personal",
                notes="Batch expense 1",
            ),
            ExpenseDTO(
                date=dt.date(2026, 2, 2),
                category="Transport",
                subcategory="Gas",
                amount=Decimal("60.00"),
                account="TWH - Personal",
                notes="Batch expense 2",
            ),
        ]

        conn = sqlite3.connect(batch_test_db)
        sync_count_before = conn.execute("SELECT COUNT(*) FROM SyncUpdate").fetchone()[0]
        conn.close()

        with HomeBudgetClient(db_path=batch_test_db, enable_sync=True) as client:
            result = client.add_expenses_batch(expenses)

        conn = sqlite3.connect(batch_test_db)
        sync_count_after = conn.execute("SELECT COUNT(*) FROM SyncUpdate").fetchone()[0]
        conn.close()

        # Should create sync entries (one per successful record)
        assert len(result.successful) == 2
        assert sync_count_after == sync_count_before + 2


class TestBatchIncomeOperations:
    """Test batch income operations."""

    def test_add_incomes_batch_from_dtos(self, batch_test_db: Path) -> None:
        """Batch add income from DTO list."""
        incomes = [
            IncomeDTO(
                date=dt.date(2026, 2, 1),
                name="Salary",
                amount=Decimal("5000.00"),
                account="TWH - Personal",
                notes="Monthly salary",
            ),
            IncomeDTO(
                date=dt.date(2026, 2, 15),
                name="Interest",
                amount=Decimal("25.50"),
                account="TWH - Personal",
                notes="Savings interest",
            ),
        ]

        with HomeBudgetClient(db_path=batch_test_db, enable_sync=False) as client:
            result = client.add_incomes_batch(incomes)

        assert len(result.successful) == 2
        assert len(result.failed) == 0
        assert all(record.key > 0 for record in result.successful)


class TestBatchTransferOperations:
    """Test batch transfer operations."""

    def test_add_transfers_batch_from_dtos(self, batch_test_db: Path) -> None:
        """Batch add transfers from DTO list."""
        transfers = [
            TransferDTO(
                date=dt.date(2026, 2, 5),
                from_account="TWH - Personal",
                to_account="30 CC Hashemis",
                amount=Decimal("100.00"),
                notes="Credit card payment",
            ),
            TransferDTO(
                date=dt.date(2026, 2, 12),
                from_account="TWH - Personal",
                to_account="30 CC Hashemis",
                amount=Decimal("150.00"),
                notes="Credit card payment",
            ),
        ]

        with HomeBudgetClient(db_path=batch_test_db, enable_sync=False) as client:
            result = client.add_transfers_batch(transfers)

        assert len(result.successful) == 2
        assert len(result.failed) == 0
        assert all(record.key > 0 for record in result.successful)


class TestBatchFileFormats:
    """Test batch operations from CSV and JSON files."""

    def test_load_expenses_from_csv(self, batch_expenses_csv: Path, batch_test_db: Path) -> None:
        """Load and process expenses from CSV file."""
        expenses = []
        with batch_expenses_csv.open("r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                expense = ExpenseDTO(
                    date=dt.datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    category=row["category"],
                    subcategory=row.get("subcategory") or None,
                    amount=Decimal(row["amount"]),
                    account=row["account"],
                    notes=row.get("notes") or None,
                )
                expenses.append(expense)

        assert len(expenses) == 5

        with HomeBudgetClient(db_path=batch_test_db, enable_sync=False) as client:
            result = client.add_expenses_batch(expenses)

        assert len(result.successful) == 5
        assert len(result.failed) == 0

    def test_load_income_from_json(self, batch_income_json: Path, batch_test_db: Path) -> None:
        """Load and process income from JSON file."""
        with batch_income_json.open("r") as f:
            data = json.load(f)

        incomes = []
        for item in data:
            income = IncomeDTO(
                date=dt.datetime.strptime(item["date"], "%Y-%m-%d").date(),
                name=item["name"],
                amount=Decimal(item["amount"]),
                account=item["account"],
                notes=item.get("notes") or None,
            )
            incomes.append(income)

        assert len(incomes) == 3

        with HomeBudgetClient(db_path=batch_test_db, enable_sync=False) as client:
            result = client.add_incomes_batch(incomes)

        assert len(result.successful) == 3
        assert len(result.failed) == 0
