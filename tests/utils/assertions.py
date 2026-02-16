from __future__ import annotations

from collections.abc import Iterable


def assert_required_keys(payload: dict, required_keys: Iterable[str]) -> None:
    missing = [key for key in required_keys if key not in payload]
    if missing:
        raise AssertionError(f"Missing required keys: {', '.join(missing)}")


def assert_operation(payload: dict, operation: str) -> None:
    if payload.get("Operation") != operation:
        raise AssertionError(
            f"Expected Operation '{operation}', got '{payload.get('Operation')}'"
        )
