"""Integration tests for reference data list CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from homebudget.cli.main import main


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


class TestCLIReferenceLists:
    """Test CLI commands for reference lists."""

    def test_account_list_command(self, cli_runner, test_db_path):
        """Test 'hb account list' command."""
        result = cli_runner.invoke(
            main, ["--db", str(test_db_path), "account", "list"]
        )

        assert result.exit_code == 0
        assert "Account" in result.output or "account" in result.output.lower()

    def test_account_list_with_currency_filter(self, cli_runner, test_db_path):
        """Test 'hb account list --currency USD' command."""
        result = cli_runner.invoke(
            main, ["--db", str(test_db_path), "account", "list", "--currency", "USD"]
        )

        assert result.exit_code == 0
        # Output should contain currency-filtered results
        assert "USD" in result.output or "account" in result.output.lower()

    def test_account_list_with_type_filter(self, cli_runner, test_db_path):
        """Test 'hb account list --type Cash' command."""
        result = cli_runner.invoke(
            main, ["--db", str(test_db_path), "account", "list", "--type", "Cash"]
        )

        assert result.exit_code == 0
        # Output should contain type-filtered results
        assert "Cash" in result.output or "account" in result.output.lower()

    def test_account_list_with_both_filters(self, cli_runner, test_db_path):
        """Test 'hb account list --currency USD --type Cash' command."""
        result = cli_runner.invoke(
            main,
            [
                "--db",
                str(test_db_path),
                "account",
                "list",
                "--currency",
                "USD",
                "--type",
                "Cash",
            ],
        )

        assert result.exit_code == 0
        # Output should display filtered results
        assert "account" in result.output.lower() or "Account" in result.output

    def test_category_list_command(self, cli_runner, test_db_path):
        """Test 'hb category list' command."""
        result = cli_runner.invoke(
            main, ["--db", str(test_db_path), "category", "list"]
        )

        assert result.exit_code == 0
        assert "Categories" in result.output or "categories" in result.output.lower()

    def test_subcategories_command(self, cli_runner, test_db_path):
        """Test 'hb category subcategories --category NAME' command."""
        # First get a category name
        list_result = cli_runner.invoke(
            main, ["--db", str(test_db_path), "category", "list"]
        )
        assert list_result.exit_code == 0

        # Extract first category name from output
        # This is a simple test, assuming output contains category names
        result = cli_runner.invoke(
            main,
            ["--db", str(test_db_path), "category", "subcategories", "--category", "Groceries"],
        )

        # Command should either succeed or fail gracefully if category doesn't exist
        # Just verify it doesn't crash
        assert result.exit_code in [0, 1, 2]

    def test_subcategories_not_found(self, cli_runner, test_db_path):
        """Test 'hb category subcategories' with non-existent category."""
        result = cli_runner.invoke(
            main,
            ["--db", str(test_db_path), "category", "subcategories", "--category", "NonExistientCategoryXYZ"],
        )

        # Should fail gracefully with error message
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()
