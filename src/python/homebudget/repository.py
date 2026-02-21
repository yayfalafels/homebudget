"""SQLite repository implementation for HomeBudget."""

from __future__ import annotations

from pathlib import Path
import datetime as dt
from decimal import Decimal
import sqlite3

from homebudget.exceptions import DuplicateError, NotFoundError
from homebudget.models import (
    ExpenseDTO,
    ExpenseRecord,
    IncomeDTO,
    IncomeRecord,
    TransferDTO,
    TransferRecord,
)
from homebudget.persistence import PersistenceBackend
from homebudget.schema import (
    DEFAULT_BILL_KEY,
    DEFAULT_CATEGORY_SPLIT,
    DEFAULT_CHECKED,
    DEFAULT_INCLUDES_RECEIPT,
    DEFAULT_IS_DETAIL_ENTRY,
    DEFAULT_MASTER_KEY,
    DEFAULT_PAYEE_KEY,
    DEFAULT_PERIODS,
    DEFAULT_RECURRING_KEY,
    FLAG_Y,
    TRANSACTION_TYPES,
)


ALLOWED_DECIMAL_PLACES = {0, 2}
DEFAULT_DECIMAL_PLACES = 2


class Repository(PersistenceBackend):
    """SQLite-backed persistence implementation."""

    def __init__(self, db_path: str | Path) -> None:
        """Create a repository for the given database path."""
        self.db_path = Path(db_path)
        self.connection: sqlite3.Connection | None = None

    @staticmethod
    def _round_currency_amount(amount: Decimal, decimal_places: int) -> Decimal:
        """Round amount to specified decimal places."""
        if decimal_places == 0:
            return amount.quantize(Decimal("1"))
        return amount.quantize(Decimal("0.01"))

    @staticmethod
    def _resolve_decimal_places(decimal_places: int | None) -> int:
        """Resolve decimal places using defaults when not provided."""
        if decimal_places is None:
            return DEFAULT_DECIMAL_PLACES
        if decimal_places not in ALLOWED_DECIMAL_PLACES:
            raise ValueError("decimal_places must be 0 or 2")
        return decimal_places

    def connect(self) -> None:
        """Open the database connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the database connection."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def begin_transaction(self) -> None:
        """Begin a database transaction."""
        self._ensure_connection()
        self.connection.execute("BEGIN")

    def commit(self) -> None:
        """Commit the current transaction."""
        self._ensure_connection()
        self.connection.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._ensure_connection()
        self.connection.rollback()

    def list_accounts(self) -> list[dict[str, object]]:
        """Return account summaries ordered by name."""
        self._ensure_connection()
        cursor = self.connection.execute(
            "SELECT key, name, accountType, balance, currency FROM Account ORDER BY name"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def insert_expense(self, expense: ExpenseDTO) -> ExpenseRecord:
        """Insert a new expense row and return the record."""
        self._ensure_connection()
        account = self._get_account(expense.account)
        category = self._get_category(expense.category)
        subcategory = self._get_subcategory(expense.subcategory)

        notes = expense.notes or ""
        amount = Decimal(expense.amount)
        currency = expense.currency or account["currency"]
        currency_amount = expense.currency_amount or amount

        amount_decimal_places = self._resolve_decimal_places(expense.amount_decimal_places)
        currency_decimal_places = self._resolve_decimal_places(
            expense.currency_amount_decimal_places
            if expense.currency_amount_decimal_places is not None
            else expense.amount_decimal_places
        )
        amount = self._round_currency_amount(amount, amount_decimal_places)
        currency_amount = self._round_currency_amount(currency_amount, currency_decimal_places)
        
        device_id_key = self._get_primary_device_key()
        device_key = self._get_next_device_key("Expense")

        duplicate = self.connection.execute(
            """
            SELECT key FROM Expense
            WHERE date = ?
              AND payFrom = ?
              AND amount = ?
              AND catKey = ?
              AND subCatKey = ?
              AND notes = ?
            """,
            (
                expense.date.isoformat(),
                account["key"],
                float(amount),
                category["key"],
                subcategory["key"],
                notes,
            ),
        ).fetchone()
        if duplicate is not None:
            raise DuplicateError(
                "Duplicate expense",
                {
                    "date": expense.date.isoformat(),
                    "account": expense.account,
                    "amount": str(amount),
                    "category": expense.category,
                    "subcategory": expense.subcategory,
                },
            )

        timestamp = dt.datetime.now().replace(microsecond=0)
        cursor = self.connection.execute(
            """
            INSERT INTO Expense (
                date,
                catKey,
                subCatKey,
                amount,
                periods,
                notes,
                isDetailEntry,
                masterKey,
                includesReceipt,
                payFrom,
                payeeKey,
                billKey,
                deviceIdKey,
                deviceKey,
                timeStamp,
                currency,
                currencyAmount,
                recurringKey,
                isCategorySplit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expense.date.isoformat(),
                category["key"],
                subcategory["key"],
                float(amount),
                DEFAULT_PERIODS,
                notes,
                DEFAULT_IS_DETAIL_ENTRY,
                DEFAULT_MASTER_KEY,
                DEFAULT_INCLUDES_RECEIPT,
                account["key"],
                DEFAULT_PAYEE_KEY,
                DEFAULT_BILL_KEY,
                device_id_key,
                device_key,
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                currency,
                str(currency_amount),
                DEFAULT_RECURRING_KEY,
                DEFAULT_CATEGORY_SPLIT,
            ),
        )
        expense_key = int(cursor.lastrowid)

        self.connection.execute(
            """
            INSERT INTO AccountTrans (
                accountKey,
                timeStamp,
                transType,
                transKey,
                transDate,
                transAmount,
                checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account["key"],
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                TRANSACTION_TYPES["expense"],
                expense_key,
                expense.date.isoformat(),
                float(amount),
                DEFAULT_CHECKED,
            ),
        )

        return ExpenseRecord(
            key=expense_key,
            date=expense.date,
            category=expense.category,
            subcategory=expense.subcategory,
            amount=amount,
            account=expense.account,
            notes=expense.notes,
            payee=expense.payee,
            currency=currency,
            currency_amount=currency_amount,
            time_stamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def get_expense(self, key: int) -> ExpenseRecord:
        """Fetch a single expense by key."""
        self._ensure_connection()
        row = self.connection.execute(
            """
            SELECT
                Expense.key,
                Expense.date,
                Expense.amount,
                Expense.notes,
                Expense.currency,
                Expense.currencyAmount,
                Expense.timeStamp,
                Account.name AS account,
                Category.name AS category,
                SubCategory.name AS subcategory
            FROM Expense
            JOIN Account ON Account.key = Expense.payFrom
            JOIN Category ON Category.key = Expense.catKey
            JOIN SubCategory ON SubCategory.key = Expense.subCatKey
            WHERE Expense.key = ?
            """,
            (key,),
        ).fetchone()
        if row is None:
            raise NotFoundError("Expense not found")
        return ExpenseRecord(
            key=row["key"],
            date=dt.date.fromisoformat(row["date"]),
            category=row["category"],
            subcategory=row["subcategory"],
            amount=Decimal(str(row["amount"])),
            account=row["account"],
            notes=row["notes"],
            payee=None,
            currency=row["currency"],
            currency_amount=Decimal(str(row["currencyAmount"]))
            if row["currencyAmount"] is not None
            else None,
            time_stamp=row["timeStamp"],
        )

    def list_expenses(
        self,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
    ) -> list[ExpenseRecord]:
        """List expenses, optionally filtered by date range."""
        self._ensure_connection()
        filters = []
        params: list[object] = []
        if start_date is not None:
            filters.append("Expense.date >= ?")
            params.append(start_date.isoformat())
        if end_date is not None:
            filters.append("Expense.date <= ?")
            params.append(end_date.isoformat())
        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        rows = self.connection.execute(
            f"""
            SELECT
                Expense.key,
                Expense.date,
                Expense.amount,
                Expense.notes,
                Expense.currency,
                Expense.currencyAmount,
                Expense.timeStamp,
                Account.name AS account,
                Category.name AS category,
                SubCategory.name AS subcategory
            FROM Expense
            JOIN Account ON Account.key = Expense.payFrom
            JOIN Category ON Category.key = Expense.catKey
            JOIN SubCategory ON SubCategory.key = Expense.subCatKey
            {where_clause}
            ORDER BY Expense.date DESC, Expense.key DESC
            """,
            params,
        ).fetchall()

        return [
            ExpenseRecord(
                key=row["key"],
                date=dt.date.fromisoformat(row["date"]),
                category=row["category"],
                subcategory=row["subcategory"],
                amount=Decimal(str(row["amount"])),
                account=row["account"],
                notes=row["notes"],
                payee=None,
                currency=row["currency"],
                currency_amount=Decimal(str(row["currencyAmount"]))
                if row["currencyAmount"] is not None
                else None,
                time_stamp=row["timeStamp"],
            )
            for row in rows
        ]

    def update_expense(
        self,
        key: int,
        amount: Decimal | str | int | float | None = None,
        notes: str | None = None,
        currency: str | None = None,
        currency_amount: Decimal | str | int | float | None = None,
        amount_decimal_places: int | None = None,
        currency_amount_decimal_places: int | None = None,
    ) -> ExpenseRecord:
        """Update an expense and return the latest record."""
        self._ensure_connection()
        updates = []
        params: list[object] = []
        normalized_amount: Decimal | None = None
        normalized_currency_amount: Decimal | None = None
        if amount is not None:
            updates.append("amount = ?")
            normalized_amount = Decimal(str(amount))
            amount_places = self._resolve_decimal_places(amount_decimal_places)
            normalized_amount = self._round_currency_amount(normalized_amount, amount_places)
            params.append(float(normalized_amount))
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if currency is not None:
            updates.append("currency = ?")
            params.append(currency)
        if currency_amount is not None:
            updates.append("currencyAmount = ?")
            normalized_currency_amount = Decimal(str(currency_amount))
            currency_places = self._resolve_decimal_places(
                currency_amount_decimal_places
                if currency_amount_decimal_places is not None
                else amount_decimal_places
            )
            normalized_currency_amount = self._round_currency_amount(
                normalized_currency_amount, currency_places
            )
            params.append(str(normalized_currency_amount))
        elif normalized_amount is not None:
            updates.append("currencyAmount = ?")
            normalized_currency_amount = normalized_amount
            params.append(str(normalized_currency_amount))
        if not updates:
            return self.get_expense(key)
        params.append(key)
        self.connection.execute(
            f"UPDATE Expense SET {', '.join(updates)} WHERE key = ?",
            params,
        )
        if normalized_amount is not None:
            self.connection.execute(
                "UPDATE AccountTrans SET transAmount = ? WHERE transType = ? AND transKey = ?",
                (float(normalized_amount), TRANSACTION_TYPES["expense"], key),
            )
        return self.get_expense(key)

    def delete_expense(self, key: int) -> None:
        """Delete an expense and related account transaction."""
        self._ensure_connection()
        self.connection.execute(
            "DELETE FROM AccountTrans WHERE transType = ? AND transKey = ?",
            (TRANSACTION_TYPES["expense"], key),
        )
        self.connection.execute("DELETE FROM Expense WHERE key = ?", (key,))

    def insert_income(self, income: IncomeDTO) -> IncomeRecord:
        """Insert a new income row and return the record."""
        self._ensure_connection()
        account = self._get_account(income.account)

        notes = income.notes or ""
        amount = Decimal(income.amount)
        currency = income.currency or account["currency"]
        currency_amount = income.currency_amount or amount

        amount_decimal_places = self._resolve_decimal_places(income.amount_decimal_places)
        currency_decimal_places = self._resolve_decimal_places(
            income.currency_amount_decimal_places
            if income.currency_amount_decimal_places is not None
            else income.amount_decimal_places
        )
        amount = self._round_currency_amount(amount, amount_decimal_places)
        currency_amount = self._round_currency_amount(currency_amount, currency_decimal_places)
        
        device_id_key = self._get_primary_device_key()
        device_key = self._get_next_device_key("Income")

        duplicate = self.connection.execute(
            """
            SELECT key FROM Income
            WHERE date = ?
              AND addIncomeTo = ?
              AND amount = ?
              AND name = ?
              AND notes = ?
            """,
            (
                income.date.isoformat(),
                account["key"],
                float(amount),
                income.name,
                notes,
            ),
        ).fetchone()
        if duplicate is not None:
            raise DuplicateError(
                "Duplicate income",
                {
                    "date": income.date.isoformat(),
                    "account": income.account,
                    "amount": str(amount),
                    "name": income.name,
                },
            )

        timestamp = dt.datetime.now().replace(microsecond=0)
        cursor = self.connection.execute(
            """
            INSERT INTO Income (
                date,
                name,
                amount,
                notes,
                addIncomeTo,
                deviceIdKey,
                deviceKey,
                timeStamp,
                currency,
                currencyAmount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                income.date.isoformat(),
                income.name,
                float(amount),
                notes,
                account["key"],
                device_id_key,
                device_key,
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                currency,
                str(currency_amount),
            ),
        )
        income_key = cursor.lastrowid

        self.connection.execute(
            """
            INSERT INTO AccountTrans (
                accountKey,
                timeStamp,
                transType,
                transKey,
                transDate,
                transAmount,
                checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account["key"],
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                TRANSACTION_TYPES["income"],
                income_key,
                income.date.isoformat(),
                float(amount),
                DEFAULT_CHECKED,
            ),
        )

        return IncomeRecord(
            key=income_key,
            date=income.date,
            name=income.name,
            amount=amount,
            account=income.account,
            notes=income.notes,
            currency=currency,
            currency_amount=currency_amount,
            time_stamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def get_income(self, key: int) -> IncomeRecord:
        """Fetch a single income record by key."""
        self._ensure_connection()
        row = self.connection.execute(
            """
            SELECT
                Income.key,
                Income.date,
                Income.name,
                Income.amount,
                Income.notes,
                Income.currency,
                Income.currencyAmount,
                Income.timeStamp,
                Account.name AS account
            FROM Income
            JOIN Account ON Account.key = Income.addIncomeTo
            WHERE Income.key = ?
            """,
            (key,),
        ).fetchone()
        if row is None:
            raise NotFoundError("Income not found")
        return IncomeRecord(
            key=row["key"],
            date=dt.date.fromisoformat(row["date"]),
            name=row["name"],
            amount=Decimal(str(row["amount"])),
            account=row["account"],
            notes=row["notes"],
            currency=row["currency"],
            currency_amount=Decimal(str(row["currencyAmount"]))
            if row["currencyAmount"] is not None
            else None,
            time_stamp=row["timeStamp"],
        )

    def list_incomes(
        self,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
    ) -> list[IncomeRecord]:
        """List income records, optionally filtered by date range."""
        self._ensure_connection()
        filters = []
        params: list[object] = []
        if start_date is not None:
            filters.append("Income.date >= ?")
            params.append(start_date.isoformat())
        if end_date is not None:
            filters.append("Income.date <= ?")
            params.append(end_date.isoformat())
        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        rows = self.connection.execute(
            f"""
            SELECT
                Income.key,
                Income.date,
                Income.name,
                Income.amount,
                Income.notes,
                Income.currency,
                Income.currencyAmount,
                Income.timeStamp,
                Account.name AS account
            FROM Income
            JOIN Account ON Account.key = Income.addIncomeTo
            {where_clause}
            ORDER BY Income.date DESC, Income.key DESC
            """,
            params,
        ).fetchall()

        return [
            IncomeRecord(
                key=row["key"],
                date=dt.date.fromisoformat(row["date"]),
                name=row["name"],
                amount=Decimal(str(row["amount"])),
                account=row["account"],
                notes=row["notes"],
                currency=row["currency"],
                currency_amount=Decimal(str(row["currencyAmount"]))
                if row["currencyAmount"] is not None
                else None,
                time_stamp=row["timeStamp"],
            )
            for row in rows
        ]

    def update_income(
        self,
        key: int,
        amount: Decimal | str | int | float | None = None,
        notes: str | None = None,
        currency: str | None = None,
        currency_amount: Decimal | str | int | float | None = None,
        amount_decimal_places: int | None = None,
        currency_amount_decimal_places: int | None = None,
    ) -> IncomeRecord:
        """Update an income record and return the latest data."""
        self._ensure_connection()
        updates = []
        params: list[object] = []
        normalized_amount: Decimal | None = None
        normalized_currency_amount: Decimal | None = None
        if amount is not None:
            updates.append("amount = ?")
            normalized_amount = Decimal(str(amount))
            amount_places = self._resolve_decimal_places(amount_decimal_places)
            normalized_amount = self._round_currency_amount(normalized_amount, amount_places)
            params.append(float(normalized_amount))
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if currency is not None:
            updates.append("currency = ?")
            params.append(currency)
        if currency_amount is not None:
            updates.append("currencyAmount = ?")
            normalized_currency_amount = Decimal(str(currency_amount))
            currency_places = self._resolve_decimal_places(
                currency_amount_decimal_places
                if currency_amount_decimal_places is not None
                else amount_decimal_places
            )
            normalized_currency_amount = self._round_currency_amount(
                normalized_currency_amount, currency_places
            )
            params.append(str(normalized_currency_amount))
        elif normalized_amount is not None:
            updates.append("currencyAmount = ?")
            normalized_currency_amount = normalized_amount
            params.append(str(normalized_currency_amount))
        if not updates:
            return self.get_income(key)
        params.append(key)
        self.connection.execute(
            f"UPDATE Income SET {', '.join(updates)} WHERE key = ?",
            params,
        )
        if normalized_amount is not None:
            self.connection.execute(
                "UPDATE AccountTrans SET transAmount = ? WHERE transType = ? AND transKey = ?",
                (float(normalized_amount), TRANSACTION_TYPES["income"], key),
            )
        return self.get_income(key)

    def delete_income(self, key: int) -> None:
        """Delete an income record and related account transaction."""
        self._ensure_connection()
        self.connection.execute(
            "DELETE FROM AccountTrans WHERE transType = ? AND transKey = ?",
            (TRANSACTION_TYPES["income"], key),
        )
        self.connection.execute("DELETE FROM Income WHERE key = ?", (key,))

    def insert_transfer(self, transfer: TransferDTO) -> TransferRecord:
        """Insert a new transfer row and return the record."""
        self._ensure_connection()
        from_account = self._get_account(transfer.from_account)
        to_account = self._get_account(transfer.to_account)

        notes = transfer.notes or ""
        amount = Decimal(transfer.amount)
        currency = transfer.currency or from_account["currency"]
        currency_amount = transfer.currency_amount or amount

        amount_decimal_places = self._resolve_decimal_places(transfer.amount_decimal_places)
        currency_decimal_places = self._resolve_decimal_places(
            transfer.currency_amount_decimal_places
            if transfer.currency_amount_decimal_places is not None
            else transfer.amount_decimal_places
        )
        amount = self._round_currency_amount(amount, amount_decimal_places)
        currency_amount = self._round_currency_amount(currency_amount, currency_decimal_places)
        
        device_id_key = self._get_primary_device_key()
        device_key = self._get_next_device_key("Transfer")

        duplicate = self.connection.execute(
            """
            SELECT key FROM Transfer
            WHERE transferDate = ?
              AND fromAccount = ?
              AND toAccount = ?
              AND amount = ?
              AND notes = ?
            """,
            (
                transfer.date.isoformat(),
                from_account["key"],
                to_account["key"],
                float(amount),
                notes,
            ),
        ).fetchone()
        if duplicate is not None:
            raise DuplicateError(
                "Duplicate transfer",
                {
                    "date": transfer.date.isoformat(),
                    "from_account": transfer.from_account,
                    "to_account": transfer.to_account,
                    "amount": str(amount),
                },
            )

        timestamp = dt.datetime.now().replace(microsecond=0)
        cursor = self.connection.execute(
            """
            INSERT INTO Transfer (
                transferDate,
                fromAccount,
                toAccount,
                amount,
                notes,
                deviceIdKey,
                deviceKey,
                currency,
                currencyAmount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transfer.date.isoformat(),
                from_account["key"],
                to_account["key"],
                float(amount),
                notes,
                device_id_key,
                device_key,
                currency,
                str(currency_amount),
            ),
        )
        transfer_key = int(cursor.lastrowid)

        # Determine transaction amounts for AccountTrans records
        # With the constraint that currency == from_account["currency"]:
        # - from_amount = currency_amount (amount in from_account currency)
        # - to_amount = amount (amount in to_account currency)
        from_amount = currency_amount
        to_amount = amount

        # Create transfer_out for from_account
        self.connection.execute(
            """
            INSERT INTO AccountTrans (
                accountKey,
                timeStamp,
                transType,
                transKey,
                transDate,
                transAmount,
                checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                from_account["key"],
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                TRANSACTION_TYPES["transfer_out"],
                transfer_key,
                transfer.date.isoformat(),
                float(from_amount),
                DEFAULT_CHECKED,
            ),
        )

        # Create transfer_in for to_account
        self.connection.execute(
            """
            INSERT INTO AccountTrans (
                accountKey,
                timeStamp,
                transType,
                transKey,
                transDate,
                transAmount,
                checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                to_account["key"],
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                TRANSACTION_TYPES["transfer_in"],
                transfer_key,
                transfer.date.isoformat(),
                float(to_amount),
                DEFAULT_CHECKED,
            ),
        )

        return TransferRecord(
            key=transfer_key,
            date=transfer.date,
            from_account=transfer.from_account,
            to_account=transfer.to_account,
            amount=amount,
            notes=transfer.notes,
            currency=currency,
            currency_amount=currency_amount,
            time_stamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def get_transfer(self, key: int) -> TransferRecord:
        """Fetch a single transfer by key."""
        self._ensure_connection()
        row = self.connection.execute(
            """
            SELECT
                Transfer.key,
                Transfer.transferDate AS date,
                Transfer.amount,
                Transfer.notes,
                Transfer.currency,
                Transfer.currencyAmount,
                from_acct.name AS from_account,
                to_acct.name AS to_account
            FROM Transfer
            JOIN Account AS from_acct ON from_acct.key = Transfer.fromAccount
            JOIN Account AS to_acct ON to_acct.key = Transfer.toAccount
            WHERE Transfer.key = ?
            """,
            (key,),
        ).fetchone()
        if row is None:
            raise NotFoundError("Transfer not found")
        return TransferRecord(
            key=row["key"],
            date=dt.date.fromisoformat(row["date"]),
            from_account=row["from_account"],
            to_account=row["to_account"],
            amount=Decimal(str(row["amount"])),
            notes=row["notes"],
            currency=row["currency"],
            currency_amount=Decimal(str(row["currencyAmount"]))
            if row["currencyAmount"] is not None
            else None,
            time_stamp=None,
        )

    def list_transfers(
        self,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
    ) -> list[TransferRecord]:
        """List transfers, optionally filtered by date range."""
        self._ensure_connection()
        query = """
            SELECT
                Transfer.key,
                Transfer.transferDate AS date,
                Transfer.amount,
                Transfer.notes,
                Transfer.currency,
                Transfer.currencyAmount,
                from_acct.name AS from_account,
                to_acct.name AS to_account
            FROM Transfer
            JOIN Account AS from_acct ON from_acct.key = Transfer.fromAccount
            JOIN Account AS to_acct ON to_acct.key = Transfer.toAccount
            WHERE 1 = 1
        """
        params = []
        if start_date is not None:
            query += " AND Transfer.transferDate >= ?"
            params.append(start_date.isoformat())
        if end_date is not None:
            query += " AND Transfer.transferDate <= ?"
            params.append(end_date.isoformat())
        query += " ORDER BY Transfer.transferDate DESC"
        
        cursor = self.connection.execute(query, params)
        rows = cursor.fetchall()
        return [
            TransferRecord(
                key=row["key"],
                date=dt.date.fromisoformat(row["date"]),
                from_account=row["from_account"],
                to_account=row["to_account"],
                amount=Decimal(str(row["amount"])),
                notes=row["notes"],
                currency=row["currency"],
                currency_amount=Decimal(str(row["currencyAmount"]))
                if row["currencyAmount"] is not None
                else None,
                time_stamp=None,
            )
            for row in rows
        ]

    def update_transfer(
        self,
        key: int,
        amount: Decimal | None = None,
        notes: str | None = None,
        currency: str | None = None,
        currency_amount: Decimal | None = None,
        amount_decimal_places: int | None = None,
        currency_amount_decimal_places: int | None = None,
    ) -> TransferRecord:
        """Update a transfer and return the latest record."""
        self._ensure_connection()
        normalized_amount = None
        updates = []
        params = []
        if amount is not None:
            normalized_amount = Decimal(str(amount))
            amount_places = self._resolve_decimal_places(amount_decimal_places)
            normalized_amount = self._round_currency_amount(normalized_amount, amount_places)
            updates.append("amount = ?")
            params.append(float(normalized_amount))
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if currency is not None:
            updates.append("currency = ?")
            params.append(currency)
        if currency_amount is not None:
            normalized_currency_amount = Decimal(str(currency_amount))
            currency_places = self._resolve_decimal_places(
                currency_amount_decimal_places
                if currency_amount_decimal_places is not None
                else amount_decimal_places
            )
            normalized_currency_amount = self._round_currency_amount(
                normalized_currency_amount, currency_places
            )
            updates.append("currencyAmount = ?")
            params.append(str(normalized_currency_amount))
        if not updates:
            return self.get_transfer(key)
        params.append(key)
        self.connection.execute(
            f"UPDATE Transfer SET {', '.join(updates)} WHERE key = ?",
            params,
        )
        if normalized_amount is not None:
            # Update both transfer_out and transfer_in amounts
            self.connection.execute(
                "UPDATE AccountTrans SET transAmount = ? WHERE transType IN (?, ?) AND transKey = ?",
                (float(normalized_amount), TRANSACTION_TYPES["transfer_out"], TRANSACTION_TYPES["transfer_in"], key),
            )
        return self.get_transfer(key)

    def delete_transfer(self, key: int) -> None:
        """Delete a transfer record and related account transactions."""
        self._ensure_connection()
        self.connection.execute(
            "DELETE FROM AccountTrans WHERE transType IN (?, ?) AND transKey = ?",
            (TRANSACTION_TYPES["transfer_out"], TRANSACTION_TYPES["transfer_in"], key),
        )
        self.connection.execute("DELETE FROM Transfer WHERE key = ?", (key,))

    def _ensure_connection(self) -> None:
        """Ensure the connection is initialized before use."""
        if self.connection is None:
            raise RuntimeError("Repository connection is not initialized")

    def _get_account(self, name: str) -> dict[str, object]:
        """Resolve an account row by name."""
        row = self.connection.execute(
            "SELECT key, currency FROM Account WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            raise NotFoundError("Account not found")
        return {
            "key": row["key"],
            "currency": row["currency"],
        }

    def _get_category(self, name: str) -> dict[str, object]:
        """Resolve a category row by name."""
        row = self.connection.execute(
            "SELECT key FROM Category WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            raise NotFoundError("Category not found")
        return {"key": row["key"]}

    def _get_subcategory(self, name: str) -> dict[str, object]:
        """Resolve a subcategory row by name."""
        row = self.connection.execute(
            "SELECT key FROM SubCategory WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            raise NotFoundError("Subcategory not found")
        return {"key": row["key"]}

    def _get_primary_device_key(self) -> int | None:
        """Return the primary device key when available."""
        row = self.connection.execute(
            "SELECT key FROM DeviceInfo WHERE isPrimary = ? AND isActive = ? "
            "ORDER BY key LIMIT 1",
            (FLAG_Y, FLAG_Y),
        ).fetchone()
        return int(row[0]) if row is not None else None

    def _get_next_device_key(self, table: str) -> int:
        """Return the next device key for a table."""
        row = self.connection.execute(
            f"SELECT COALESCE(MAX(deviceKey), 0) + 1 FROM {table}"
        ).fetchone()
        return int(row[0]) if row is not None else 1
