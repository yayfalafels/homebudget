from __future__ import annotations

from homebudget.exceptions import DuplicateError


def test_duplicate_error_details() -> None:
    details = {
        "date": "2026-02-16",
        "amount": "25.50",
        "account": "Wallet",
    }
    error = DuplicateError("Duplicate expense", details)

    assert error.details == details
    assert "Duplicate expense" in str(error)
