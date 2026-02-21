"""System integration tests for forex inference behavior."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from homebudget import ExpenseDTO, IncomeDTO, TransferDTO
from homebudget.client import HomeBudgetClient


BASE_ACCOUNT = "Cash TWH SGD"
NON_BASE_ACCOUNT = "TWH IB USD"
NON_BASE_CURRENCY = "USD"
EXPENSE_CATEGORY = "Food (Basic)"
EXPENSE_SUBCATEGORY = "Groceries"
INCOME_NAME = "Salary and Wages"
INPUT_AMOUNT = Decimal("100.00")
FOREX_RATE = Decimal("1.35")


def _patch_rate(client: HomeBudgetClient, monkeypatch: pytest.MonkeyPatch) -> None:
    if not hasattr(client, "_get_forex_rate"):
        pytest.skip("Forex rate inference not implemented")
    monkeypatch.setattr(client, "_get_forex_rate", lambda _: float(FOREX_RATE))


@pytest.mark.sit
def test_expense_amount_only_infers_currency_amount(
    test_db_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expense = ExpenseDTO(
        date=dt.date(2026, 2, 16),
        category=EXPENSE_CATEGORY,
        subcategory=EXPENSE_SUBCATEGORY,
        amount=INPUT_AMOUNT,
        account=NON_BASE_ACCOUNT,
        notes="Forex expense inference",
    )

    with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
        _patch_rate(client, monkeypatch)
        saved = client.add_expense(expense)

    expected_amount = (INPUT_AMOUNT * FOREX_RATE).quantize(Decimal("0.01"))
    assert saved.currency == NON_BASE_CURRENCY
    assert saved.currency_amount == INPUT_AMOUNT
    assert saved.amount == expected_amount


@pytest.mark.sit
def test_income_amount_only_infers_currency_amount(
    test_db_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    income = IncomeDTO(
        date=dt.date(2026, 2, 16),
        name=INCOME_NAME,
        amount=INPUT_AMOUNT,
        account=NON_BASE_ACCOUNT,
        notes="Forex income inference",
    )

    with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
        _patch_rate(client, monkeypatch)
        saved = client.add_income(income)

    expected_amount = (INPUT_AMOUNT * FOREX_RATE).quantize(Decimal("0.01"))
    assert saved.currency == NON_BASE_CURRENCY
    assert saved.currency_amount == INPUT_AMOUNT
    assert saved.amount == expected_amount


@pytest.mark.sit
def test_transfer_amount_only_infers_currency_amount(
    test_db_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer = TransferDTO(
        date=dt.date(2026, 2, 20),
        from_account=BASE_ACCOUNT,
        to_account=NON_BASE_ACCOUNT,
        amount=INPUT_AMOUNT,
        notes="Forex transfer inference",
    )

    with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
        _patch_rate(client, monkeypatch)
        saved = client.add_transfer(transfer)

    # Currency and currency_amount must match from_account (BASE_ACCOUNT = SGD)
    # from_account is base, to_account is foreign
    # User amount is in base (100 SGD), transfer to foreign (USD)
    # currency = SGD, currency_amount = 100 (in SGD)
    # amount = 100 / 1.35 = 74.074... (in USD, to_account currency, rounded to 2 decimal places)
    expected_to_amount = (INPUT_AMOUNT / FOREX_RATE).quantize(Decimal("0.01"))
    assert saved.currency == "SGD"
    assert saved.currency_amount == INPUT_AMOUNT
    assert saved.amount == expected_to_amount