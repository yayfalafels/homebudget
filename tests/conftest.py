"""Pytest configuration and fixtures for system integration tests.

These fixtures provide headless test databases for SIT tests only.
UAT tests use live operational HomeBudget databases connected to apps.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import sys

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "python"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _copy_fixture(tmp_path: Path, fixture_name: str) -> Path:
    """Copy a headless test database fixture to temporary directory for SIT tests."""
    source = FIXTURES_DIR / fixture_name
    target = tmp_path / fixture_name
    shutil.copyfile(source, target)
    return target


@pytest.fixture()
def test_db_path(tmp_path: Path) -> Path:
    """Headless test database with sample data for SIT tests."""
    path = _copy_fixture(tmp_path, "test_database.db")
    yield path
    # Windows-specific: ensure connections are closed before cleanup
    import gc
    gc.collect()
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            pass  # File still in use, OS will clean up temp directory


@pytest.fixture()
def empty_db_path(tmp_path: Path) -> Path:
    """Headless test database with schema only for SIT tests."""
    path = _copy_fixture(tmp_path, "empty_database.db")
    yield path
    import gc
    gc.collect()
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            pass


@pytest.fixture()
def sync_test_db_path(tmp_path: Path) -> Path:
    """Headless test database with DeviceInfo configured for SIT tests."""
    path = _copy_fixture(tmp_path, "sync_test.db")
    yield path
    import gc
    gc.collect()
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            pass


@pytest.fixture()
def sample_expense_payload() -> dict:
    return {
        "date": "2026-02-16",
        "category": "Dining",
        "subcategory": "Restaurant",
        "amount": "25.50",
        "account": "Wallet",
        "notes": "Fixture expense",
    }
