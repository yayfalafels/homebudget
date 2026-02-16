from __future__ import annotations

from pathlib import Path
import datetime as dt
from decimal import Decimal
import sqlite3

from homebudget.exceptions import DuplicateError
from homebudget.models import ExpenseDTO, ExpenseRecord
from homebudget.schema import TRANSACTION_TYPES


class Repository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.connection: sqlite3.Connection | None = None

    def connect(self) -> None:
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def begin_transaction(self) -> None:
        self._ensure_connection()
        self.connection.execute("BEGIN")

    def commit(self) -> None:
        self._ensure_connection()
        self.connection.commit()

    def rollback(self) -> None:
        self._ensure_connection()
        self.connection.rollback()

    def list_accounts(self) -> list[dict[str, object]]:
        self._ensure_connection()
        cursor = self.connection.execute(
            "SELECT key, name, accountType, balance, currency FROM Account ORDER BY name"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def insert_expense(self, expense: ExpenseDTO) -> ExpenseRecord:
        self._ensure_connection()
        account = self._get_account(expense.account)
        category = self._get_category(expense.category)
        subcategory = self._get_subcategory(expense.subcategory)

        notes = expense.notes or ""
        amount = Decimal(expense.amount)
        currency = expense.currency or account["currency"]
        currency_amount = expense.currency_amount or amount
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
                1,
                notes,
                "Y",
                -1,
                "N",
                account["key"],
                0,
                0,
                device_id_key,
                device_key,
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                currency,
                str(currency_amount),
                0,
                "N",
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
                "N",
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
            raise ValueError("Expense not found")
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

    def list_expenses(self, start_date=None, end_date=None) -> list[ExpenseRecord]:
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

    def update_expense(self, key: int, amount=None, notes: str | None = None) -> ExpenseRecord:
        self._ensure_connection()
        updates = []
        params: list[object] = []
        if amount is not None:
            updates.append("amount = ?")
            params.append(float(Decimal(str(amount))))
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if not updates:
            return self.get_expense(key)
        params.append(key)
        self.connection.execute(
            f"UPDATE Expense SET {', '.join(updates)} WHERE key = ?",
            params,
        )
        return self.get_expense(key)

    def delete_expense(self, key: int) -> None:
        self._ensure_connection()
        self.connection.execute(
            "DELETE FROM AccountTrans WHERE transType = ? AND transKey = ?",
            (TRANSACTION_TYPES["expense"], key),
        )
        self.connection.execute("DELETE FROM Expense WHERE key = ?", (key,))

    def _ensure_connection(self) -> None:
        if self.connection is None:
            raise RuntimeError("Repository connection is not initialized")

    def _get_account(self, name: str) -> dict[str, object]:
        row = self.connection.execute(
            "SELECT key, currency FROM Account WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            raise ValueError("Account not found")
        return {
            "key": row["key"],
            "currency": row["currency"],
        }

    def _get_category(self, name: str) -> dict[str, object]:
        row = self.connection.execute(
            "SELECT key FROM Category WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            raise ValueError("Category not found")
        return {"key": row["key"]}

    def _get_subcategory(self, name: str) -> dict[str, object]:
        row = self.connection.execute(
            "SELECT key FROM SubCategory WHERE name = ?",
            (name,),
        ).fetchone()
        if row is None:
            raise ValueError("Subcategory not found")
        return {"key": row["key"]}

    def _get_primary_device_key(self) -> int | None:
        row = self.connection.execute(
            "SELECT key FROM DeviceInfo WHERE isPrimary = 'Y' AND isActive = 'Y' "
            "ORDER BY key LIMIT 1"
        ).fetchone()
        return int(row[0]) if row is not None else None

    def _get_next_device_key(self, table: str) -> int:
        row = self.connection.execute(
            f"SELECT COALESCE(MAX(deviceKey), 0) + 1 FROM {table}"
        ).fetchone()
        return int(row[0]) if row is not None else 1
