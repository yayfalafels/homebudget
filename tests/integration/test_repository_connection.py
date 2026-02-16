from __future__ import annotations

from pathlib import Path

from homebudget.repository import Repository


def test_repository_connection(test_db_path: Path) -> None:
    repo = Repository(test_db_path)
    repo.connect()
    try:
        assert repo.connection is not None
    finally:
        repo.close()


def test_repository_read_accounts(test_db_path: Path) -> None:
    repo = Repository(test_db_path)
    repo.connect()
    try:
        accounts = repo.list_accounts()
        assert accounts
        assert "name" in accounts[0]
    finally:
        repo.close()
