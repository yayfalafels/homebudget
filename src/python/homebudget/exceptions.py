from __future__ import annotations

from typing import Any


class DuplicateError(Exception):
    def __init__(self, message: str, details: dict[str, Any]) -> None:
        super().__init__(message)
        self.details = details
