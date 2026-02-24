"""Integration tests for reference data list features."""

from __future__ import annotations

import sqlite3

import pytest

from homebudget.client import HomeBudgetClient
from homebudget.exceptions import NotFoundError
from homebudget.models import AccountRecord, CategoryRecord, SubcategoryRecord
from homebudget.repository import Repository


def _get_connection(db_path: str) -> sqlite3.Connection:
    """Create a database connection for test setup."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


class TestRepositoryReferenceLists:
    """Test Repository reference list query methods."""

    def test_get_accounts(self, test_db_path):
        """Repository.get_accounts() returns all accounts ordered by name."""
        repo = Repository(str(test_db_path))
        repo.connect()

        try:
            accounts = repo.get_accounts()

            assert isinstance(accounts, list)
            assert len(accounts) > 0

            # Verify each account has the required fields
            for account in accounts:
                assert isinstance(account, dict)
                assert "key" in account
                assert "name" in account
                assert "accountType" in account
                assert "balance" in account
                assert "currency" in account

            # Verify accounts are ordered by name
            names = [acc["name"] for acc in accounts]
            assert names == sorted(names), "Accounts should be ordered by name"

        finally:
            repo.close()

    def test_get_categories(self, test_db_path):
        """Repository.get_categories() returns categories ordered by seqNum."""
        repo = Repository(str(test_db_path))
        repo.connect()

        try:
            categories = repo.get_categories()

            assert isinstance(categories, list)
            assert len(categories) > 0

            # Verify each category has the required fields
            for category in categories:
                assert isinstance(category, dict)
                assert "key" in category
                assert "name" in category
                assert "seqNum" in category

            # Verify categories are ordered by seqNum
            seqnums = [cat["seqNum"] for cat in categories]
            assert seqnums == sorted(seqnums), "Categories should be ordered by seqNum"

        finally:
            repo.close()

    def test_get_subcategories_by_category(self, test_db_path):
        """Repository.get_subcategories(key) returns subcategories ordered by seqNum."""
        repo = Repository(str(test_db_path))
        repo.connect()

        try:
            # First get a category to query subcategories for
            categories = repo.get_categories()
            assert len(categories) > 0

            category = categories[0]
            category_key = category["key"]

            # Query subcategories for this category
            subcategories = repo.get_subcategories(category_key)

            assert isinstance(subcategories, list)
            # Subcategories may be empty for some categories, so we don't require len > 0

            # Verify each subcategory has the required fields
            for subcat in subcategories:
                assert isinstance(subcat, dict)
                assert "key" in subcat
                assert "catKey" in subcat
                assert "name" in subcat
                assert "seqNum" in subcat
                # Verify catKey matches the queried category
                assert subcat["catKey"] == category_key

            # Verify subcategories are ordered by seqNum
            if len(subcategories) > 1:
                seqnums = [subcat["seqNum"] for subcat in subcategories]
                assert seqnums == sorted(
                    seqnums
                ), "Subcategories should be ordered by seqNum"

        finally:
            repo.close()


class TestClientReferenceLists:
    """Test HomeBudgetClient reference list wrapper methods."""

    def test_client_get_accounts(self, test_db_path):
        """Client.get_accounts() returns list of AccountRecord."""
        with HomeBudgetClient(str(test_db_path)) as client:
            accounts = client.get_accounts()

            assert isinstance(accounts, list)
            assert len(accounts) > 0

            # Verify each is an AccountRecord
            for account in accounts:
                assert isinstance(account, AccountRecord)
                assert account.key is not None
                assert isinstance(account.name, str)
                assert isinstance(account.accountType, str)
                assert account.balance is not None
                assert isinstance(account.currency, str)

            # Verify ordered by name
            names = [acc.name for acc in accounts]
            assert names == sorted(names), "Accounts should be ordered by name"

    def test_client_get_accounts_filter_by_currency(self, test_db_path):
        """Client.get_accounts(currency=) filters by currency."""
        with HomeBudgetClient(str(test_db_path)) as client:
            all_accounts = client.get_accounts()
            assert len(all_accounts) > 0

            # Get a sample currency from the first account
            sample_currency = all_accounts[0].currency

            # Query with currency filter
            filtered = client.get_accounts(currency=sample_currency)

            # Verify all results match the filter
            for account in filtered:
                assert account.currency == sample_currency

            # Verify we got a subset (or same set if only one currency)
            assert len(filtered) <= len(all_accounts)

    def test_client_get_accounts_filter_by_type(self, test_db_path):
        """Client.get_accounts(account_type=) filters by account type."""
        with HomeBudgetClient(str(test_db_path)) as client:
            all_accounts = client.get_accounts()
            assert len(all_accounts) > 0

            # Get a sample account type from the first account
            sample_type = all_accounts[0].accountType

            # Query with type filter
            filtered = client.get_accounts(account_type=sample_type)

            # Verify all results match the filter
            for account in filtered:
                assert account.accountType == sample_type

            # Verify we got a subset (or same set if only one type)
            assert len(filtered) <= len(all_accounts)

    def test_client_get_accounts_filter_by_both(self, test_db_path):
        """Client.get_accounts() with both currency and type filters."""
        with HomeBudgetClient(str(test_db_path)) as client:
            all_accounts = client.get_accounts()
            assert len(all_accounts) > 0

            # Get sample currency and type
            sample_currency = all_accounts[0].currency
            sample_type = all_accounts[0].accountType

            # Query with both filters
            filtered = client.get_accounts(
                currency=sample_currency, account_type=sample_type
            )

            # Verify all results match both filters
            for account in filtered:
                assert account.currency == sample_currency
                assert account.accountType == sample_type

            # Verify we got a subset
            assert len(filtered) <= len(all_accounts)

    def test_client_get_categories(self, test_db_path):
        """Client.get_categories() returns list of CategoryRecord."""
        with HomeBudgetClient(str(test_db_path)) as client:
            categories = client.get_categories()

            assert isinstance(categories, list)
            assert len(categories) > 0

            # Verify each is a CategoryRecord
            for category in categories:
                assert isinstance(category, CategoryRecord)
                assert category.key is not None
                assert isinstance(category.name, str)
                assert isinstance(category.seqNum, int)

            # Verify ordered by seqNum
            seqnums = [cat.seqNum for cat in categories]
            assert seqnums == sorted(
                seqnums
            ), "Categories should be ordered by seqNum"

    def test_client_get_subcategories(self, test_db_path):
        """Client.get_subcategories(name) resolves category and returns SubcategoryRecord list."""
        with HomeBudgetClient(str(test_db_path)) as client:
            # Get a category name from the database
            categories = client.get_categories()
            assert len(categories) > 0

            category_name = categories[0].name

            # Query subcategories for this category
            subcategories = client.get_subcategories(category_name)

            assert isinstance(subcategories, list)
            # Subcategories may be empty for some categories

            # Verify each is a SubcategoryRecord
            for subcat in subcategories:
                assert isinstance(subcat, SubcategoryRecord)
                assert subcat.key is not None
                assert subcat.categoryKey is not None
                assert subcat.categoryName == category_name
                assert isinstance(subcat.name, str)
                assert isinstance(subcat.seqNum, int)

            # Verify ordered by seqNum
            if len(subcategories) > 1:
                seqnums = [subcat.seqNum for subcat in subcategories]
                assert seqnums == sorted(
                    seqnums
                ), "Subcategories should be ordered by seqNum"

    def test_client_get_subcategories_not_found(self, test_db_path):
        """Client.get_subcategories() raises NotFoundError for non-existent category."""
        with HomeBudgetClient(str(test_db_path)) as client:
            with pytest.raises(NotFoundError):
                client.get_subcategories("NonExistentCategoryName")
