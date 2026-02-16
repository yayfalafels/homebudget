from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from homebudget.models import ExpenseDTO


def test_expense_dto_required_fields() -> None:
    expense = ExpenseDTO(
        date=dt.date(2026, 2, 16),
        category="Dining",
        subcategory="Restaurant",
        amount=Decimal("25.50"),
        account="Wallet",
    )

    assert expense.notes is None
    assert expense.payee is None
    assert expense.currency is None
    assert expense.currency_amount is None
    assert expense.amount == Decimal("25.50")


def test_expense_dto_validation() -> None:
    with pytest.raises(ValueError):
        ExpenseDTO(
            date=dt.date(2026, 2, 16),
            category="",
            subcategory="Restaurant",
            amount=Decimal("25.50"),
            account="Wallet",
        )

    with pytest.raises(ValueError):
        ExpenseDTO(
            date=dt.date(2026, 2, 16),
            category="Dining",
            subcategory="Restaurant",
            amount=Decimal("0"),
            account="Wallet",
        )


def test_expense_dto_all_fields() -> None:
    expense = ExpenseDTO(
        date=dt.date(2026, 2, 16),
        category="Dining",
        subcategory="Restaurant",
        amount=Decimal("25.50"),
        account="Wallet",
        notes="Dinner",
        payee="Local Cafe",
        currency="SGD",
        currency_amount=Decimal("25.50"),
    )

    assert expense.notes == "Dinner"
    assert expense.payee == "Local Cafe"
    assert expense.currency == "SGD"
    assert expense.currency_amount == Decimal("25.50")
