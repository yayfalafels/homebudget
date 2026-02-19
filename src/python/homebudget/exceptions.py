"""Custom exception types for HomeBudget."""

from __future__ import annotations

from typing import Any


class DuplicateError(Exception):
    """Raised when a duplicate record is detected."""

    def __init__(self, message: str, details: dict[str, Any]) -> None:
        super().__init__(message)
        self.details = details


class NotFoundError(Exception):
    """Raised when a requested record does not exist."""
