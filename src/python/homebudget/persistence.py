"""Persistence interfaces for HomeBudget storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class PersistenceBackend(ABC):
    """Abstract interface for repository backends."""

    @abstractmethod
    def __init__(self, db_path: str | Path) -> None:
        """Initialize the backend with a storage path."""

    @abstractmethod
    def connect(self) -> None:
        """Establish a backend connection."""

    @abstractmethod
    def close(self) -> None:
        """Close the backend connection."""

    @abstractmethod
    def begin_transaction(self) -> None:
        """Start a transaction."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the active transaction."""

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the active transaction."""

    @abstractmethod
    def list_accounts(self) -> list[dict[str, Any]]:
        """Return account summary rows."""

    @abstractmethod
    def get_accounts(self) -> list[dict[str, Any]]:
        """Return account reference list ordered by name."""

    @abstractmethod
    def get_categories(self) -> list[dict[str, Any]]:
        """Return category reference list ordered by seqNum."""

    @abstractmethod
    def get_subcategories(self, category_key: int) -> list[dict[str, Any]]:
        """Return subcategory reference list for the given category, ordered by seqNum."""

