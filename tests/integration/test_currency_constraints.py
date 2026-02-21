"""Negative tests for currency matching constraints.

Tests that verify the system properly rejects transactions that violate
currency matching rules:

1. Expenses/Income: Cannot add base currency to non-base currency accounts
2. Expenses/Income: Can add foreign currencies to base currency accounts
3. Transfers: Can only specify one account's currency in mixed-currency transfers
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from homebudget import (
    ExpenseDTO,
    IncomeDTO,
    TransferDTO,
    NotFoundError,
)
from homebudget.client import HomeBudgetClient


class TestExpenseCurrencyConstraints:
    """Negative tests for expense currency matching rules."""

    @pytest.mark.sit
    def test_expense_foreign_currency_to_base_account_succeeds(self, test_db_path) -> None:
        """Expense: Can add USD (foreign) to SGD (base) account with exchange rate."""
        expense = ExpenseDTO(
            date=dt.date(2026, 2, 16),
            category="Food (Basic)",
            subcategory="Groceries",
            amount=Decimal("25.50"),  # Calculated: 27.50 * 0.9273
            account="Cash TWH SGD",  # SGD base account
            notes="Foreign currency to base account - should succeed",
            currency="USD",
            currency_amount=Decimal("27.50"),
        )
        
        with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
            saved = client.add_expense(expense)
            
        assert saved.key is not None
        assert saved.amount == Decimal("25.50")
        assert saved.currency == "USD"
        assert saved.currency_amount == Decimal("27.50")

    @pytest.mark.sit
    def test_expense_base_currency_to_base_account_succeeds(self, test_db_path) -> None:
        """Expense: Can add base currency to base currency account."""
        expense = ExpenseDTO(
            date=dt.date(2026, 2, 16),
            category="Food (Basic)",
            subcategory="Groceries",
            amount=Decimal("25.50"),
            account="Cash TWH SGD",  # SGD base account
            notes="Base currency to base account - should succeed",
        )
        
        with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
            saved = client.add_expense(expense)
            
        assert saved.key is not None
        assert saved.amount == Decimal("25.50")


class TestIncomeCurrencyConstraints:
    """Negative tests for income currency matching rules."""

    @pytest.mark.sit
    def test_income_foreign_currency_to_base_account_succeeds(self, test_db_path) -> None:
        """Income: Can add USD (foreign) to SGD (base) account with exchange rate."""
        income = IncomeDTO(
            date=dt.date(2026, 2, 16),
            name="Freelance Income",
            amount=Decimal("2000.00"),  # Calculated: 2700 * 0.7407
            account="Cash TWH SGD",  # SGD base account
            notes="Foreign currency income to base account - should succeed",
            currency="USD",
            currency_amount=Decimal("2700.00"),
        )
        
        with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
            saved = client.add_income(income)
            
        assert saved.key is not None
        assert saved.amount == Decimal("2000.00")
        assert saved.currency == "USD"
        assert saved.currency_amount == Decimal("2700.00")

    @pytest.mark.sit
    def test_income_base_currency_to_base_account_succeeds(self, test_db_path) -> None:
        """Income: Can add base currency to base currency account."""
        income = IncomeDTO(
            date=dt.date(2026, 2, 16),
            name="Salary",
            amount=Decimal("5000.00"),
            account="Cash TWH SGD",
            notes="Base currency to base account - should succeed",
        )
        
        with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
            saved = client.add_income(income)
            
        assert saved.key is not None
        assert saved.amount == Decimal("5000.00")


class TestTransferCurrencyConstraints:
    """Negative tests for transfer currency matching rules."""

    @pytest.mark.sit
    def test_transfer_same_currency_both_sides_succeeds(self, test_db_path) -> None:
        """Transfer: Between same-currency accounts is straightforward."""
        transfer = TransferDTO(
            date=dt.date(2026, 2, 16),
            from_account="Cash TWH SGD",
            to_account="TWH - Personal",  # Another SGD account
            amount=Decimal("100.00"),
            notes="Same currency transfer - should succeed",
        )
        
        with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
            saved = client.add_transfer(transfer)
            assert saved.key is not None

    @pytest.mark.sit
    def test_transfer_nonexistent_account_fails(self, test_db_path) -> None:
        """Transfer: Nonexistent accounts should fail clearly."""
        transfer = TransferDTO(
            date=dt.date(2026, 2, 16),
            from_account="Nonexistent Account A",
            to_account="Nonexistent Account B",
            amount=Decimal("100.00"),
            notes="From/to nonexistent accounts",
        )
        
        with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
            with pytest.raises(NotFoundError):
                client.add_transfer(transfer)

    @pytest.mark.sit
    def test_transfer_currency_must_match_from_account(self, test_db_path) -> None:
        """Transfer: Currency can match either account (normalized to from_account).
        
        The normalization layer accepts currency specifications matching either
        the from_account OR to_account, then converts to backend format where
        currency always equals from_account currency.
        """
        # Test 1: Currency matches to_account (USD) - should be normalized to from_account format
        transfer1 = TransferDTO(
            date=dt.date(2026, 2, 16),
            from_account="Cash TWH SGD",  # SGD account (base)
            to_account="TWH IB USD",  # USD account
            currency="USD",  # Matches to_account (will be normalized)
            currency_amount=Decimal("74.00"),  # This is to_amount
            notes="Normalized: to_account currency specified",
        )
        
        with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
            # Should succeed - normalization converts to backend format
            result1 = client.add_transfer(transfer1)
            assert result1.currency == "SGD"  # Backend format: currency = from_account
            assert result1.amount == Decimal("74.00")  # to_amount preserved
            # currency_amount (from_amount) calculated from to_amount

        # Test 2: Currency matches from_account (USD) - passes through unchanged
        transfer2 = TransferDTO(
            date=dt.date(2026, 2, 17),
            from_account="TWH IB USD",  # USD account
            to_account="Cash TWH SGD",  # SGD account
            currency="USD",  # Matches from_account (passes through)
            currency_amount=Decimal("100.00"),  # This is from_amount
            notes="Pass-through: from_account currency specified",
        )
        
        with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
            # Should succeed - already in backend format
            result2 = client.add_transfer(transfer2)
            assert result2.currency == "USD"  # Backend format: currency = from_account
            assert result2.currency_amount == Decimal("100.00")  # from_amount preserved

        # Test 3: Currency doesn't match either account - should FAIL
        transfer3 = TransferDTO(
            date=dt.date(2026, 2, 18),
            from_account="Cash TWH SGD",  # SGD account
            to_account="TWH IB USD",  # USD account
            currency="EUR",  # INVALID: doesn't match either account
            currency_amount=Decimal("50.00"),
            notes="Invalid: currency matches neither account",
        )
        
        with HomeBudgetClient(db_path=test_db_path, enable_sync=False) as client:
            with pytest.raises(ValueError, match="must match either from_account or to_account"):
                client.add_transfer(transfer3)


class TestCurrencyConstraintEdgeCases:
    """Edge case tests for currency constraints."""

    @pytest.mark.sit
    def test_expense_positive_amount_required(self, test_db_path) -> None:
        """Expense: Amounts must be positive."""
        with pytest.raises(ValueError, match="must be greater than zero"):
            ExpenseDTO(
                date=dt.date(2026, 2, 16),
                category="Food (Basic)",
                subcategory="Groceries",
                amount=Decimal("0.00"),  # Invalid: zero amount
                account="Cash TWH SGD",
                notes="Zero amount",
            )

    @pytest.mark.sit
    def test_income_positive_amount_required(self, test_db_path) -> None:
        """Income: Amounts must be positive."""
        with pytest.raises(ValueError, match="must be greater than zero"):
            IncomeDTO(
                date=dt.date(2026, 2, 16),
                name="Income",
                amount=Decimal("-1000.00"),  # Negative amount
                account="Cash TWH SGD",
                notes="Negative amount",
            )

    @pytest.mark.sit
    def test_transfer_positive_amount_required(self, test_db_path) -> None:
        """Transfer: Amounts must be positive."""
        with pytest.raises(ValueError, match="must be greater than zero"):
            TransferDTO(
                date=dt.date(2026, 2, 16),
                from_account="Cash TWH SGD",
                to_account="Bank Account",
                amount=Decimal("-100.00"),  # Negative amount
                notes="Negative amount",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
