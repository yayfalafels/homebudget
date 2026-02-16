from __future__ import annotations

from pathlib import Path
import json
import os

from homebudget.models import ExpenseDTO, ExpenseRecord
from homebudget.repository import Repository
from homebudget.sync import SyncUpdateManager


class HomeBudgetClient:
    def __init__(self, db_path: str | Path | None = None, enable_sync: bool = True) -> None:
        self.db_path = self._resolve_db_path(db_path)
        self.enable_sync = enable_sync
        self.repository = Repository(self.db_path)

    def __enter__(self) -> "HomeBudgetClient":
        self.repository.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self.repository.close()

    def _resolve_db_path(self, db_path: str | Path | None) -> Path:
        if db_path is not None:
            return Path(db_path)
        config_path = (
            Path(os.environ["USER_PROFILE"]) / "OneDrive" / "Documents" / "HomeBudgetData" / "hb-config.json"
        )
        if not config_path.exists():
            raise ValueError("db_path is required when config file is missing")
        with config_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        resolved = payload.get("db_path")
        if not resolved:
            raise ValueError("db_path is missing in config file")
        return Path(resolved)

    def add_expense(self, expense: ExpenseDTO) -> ExpenseRecord:
        self.repository.begin_transaction()
        try:
            record = self.repository.insert_expense(expense)
            if self.enable_sync:
                manager = SyncUpdateManager(self.repository.connection)
                manager.create_expense_update(record)
            self.repository.commit()
            return record
        except Exception:
            self.repository.rollback()
            raise

    def get_expense(self, key: int) -> ExpenseRecord:
        return self.repository.get_expense(key)

    def list_expenses(
        self,
        start_date=None,
        end_date=None,
    ) -> list[ExpenseRecord]:
        return self.repository.list_expenses(start_date=start_date, end_date=end_date)

    def update_expense(
        self,
        key: int,
        amount=None,
        notes: str | None = None,
    ) -> ExpenseRecord:
        self.repository.begin_transaction()
        try:
            record = self.repository.update_expense(key=key, amount=amount, notes=notes)
            self.repository.commit()
            return record
        except Exception:
            self.repository.rollback()
            raise

    def delete_expense(self, key: int) -> None:
        self.repository.begin_transaction()
        try:
            self.repository.delete_expense(key)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise
