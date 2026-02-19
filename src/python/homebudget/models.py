"""Domain models and data transfer objects."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from decimal import Decimal
from typing import Any


def _ensure_date(value: dt.date | dt.datetime) -> dt.date:
    """Normalize a date or datetime to a date."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    raise ValueError("Date must be a datetime.date")


def _ensure_non_empty(value: str, field_name: str) -> str:
    """Validate required text fields."""
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _ensure_decimal(value: Decimal | str | int | float, field_name: str) -> Decimal:
    """Parse and validate positive decimal values."""
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal") from exc
    if amount <= Decimal("0"):
        raise ValueError(f"{field_name} must be greater than zero")
    return amount


@dataclass(frozen=True)
class ExpenseDTO:
    """Validated expense input for persistence."""
    date: dt.date
    category: str
    subcategory: str
    amount: Decimal
    account: str
    notes: str | None = None
    payee: str | None = None
    currency: str | None = None
    currency_amount: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "date", _ensure_date(self.date))
        object.__setattr__(self, "category", _ensure_non_empty(self.category, "Category"))
        object.__setattr__(
            self, "subcategory", _ensure_non_empty(self.subcategory, "Subcategory")
        )
        object.__setattr__(self, "account", _ensure_non_empty(self.account, "Account"))
        object.__setattr__(self, "amount", _ensure_decimal(self.amount, "Amount"))
        self._validate_currency()

    def _validate_currency(self) -> None:
        """Validate currency fields."""
        if self.currency_amount is None and self.currency is None:
            return
        if self.currency is not None and not self.currency.strip():
            raise ValueError("Currency must not be empty when provided")
        if self.currency is not None and self.currency_amount is None:
            raise ValueError("currency_amount is required when currency is set")
        if self.currency_amount is not None:
            object.__setattr__(
                self, "currency_amount", _ensure_decimal(self.currency_amount, "currency_amount")
            )


@dataclass(frozen=True)
class ExpenseRecord:
    """Persisted expense record from storage."""
    key: int
    date: dt.date
    category: str
    subcategory: str
    amount: Decimal
    account: str
    notes: str | None
    payee: str | None
    currency: str | None
    currency_amount: Decimal | None
    time_stamp: str


@dataclass(frozen=True)
class IncomeDTO:
    """Validated income input for persistence."""
    date: dt.date
    name: str
    amount: Decimal
    account: str
    notes: str | None = None
    currency: str | None = None
    currency_amount: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "date", _ensure_date(self.date))
        object.__setattr__(self, "name", _ensure_non_empty(self.name, "Name"))
        object.__setattr__(self, "account", _ensure_non_empty(self.account, "Account"))
        object.__setattr__(self, "amount", _ensure_decimal(self.amount, "Amount"))
        self._validate_currency()

    def _validate_currency(self) -> None:
        """Validate currency fields."""
        if self.currency_amount is None and self.currency is None:
            return
        if self.currency is not None and not self.currency.strip():
            raise ValueError("Currency must not be empty when provided")
        if self.currency is not None and self.currency_amount is None:
            raise ValueError("currency_amount is required when currency is set")
        if self.currency_amount is not None:
            object.__setattr__(
                self, "currency_amount", _ensure_decimal(self.currency_amount, "currency_amount")
            )


@dataclass(frozen=True)
class IncomeRecord:
    """Persisted income record from storage."""
    key: int
    date: dt.date
    name: str
    amount: Decimal
    account: str
    notes: str | None
    currency: str | None
    currency_amount: Decimal | None
    time_stamp: str


@dataclass(frozen=True)
class TransferDTO:
    """Validated transfer input for persistence."""
    date: dt.date
    from_account: str
    to_account: str
    amount: Decimal
    notes: str | None = None
    currency: str | None = None
    currency_amount: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "date", _ensure_date(self.date))
        object.__setattr__(
            self, "from_account", _ensure_non_empty(self.from_account, "From account")
        )
        object.__setattr__(
            self, "to_account", _ensure_non_empty(self.to_account, "To account")
        )
        if self.from_account == self.to_account:
            raise ValueError("From account and to account must differ")
        object.__setattr__(self, "amount", _ensure_decimal(self.amount, "Amount"))
        self._validate_currency()

    def _validate_currency(self) -> None:
        """Validate currency fields."""
        if self.currency_amount is None and self.currency is None:
            return
        if self.currency is not None and not self.currency.strip():
            raise ValueError("Currency must not be empty when provided")
        if self.currency is not None and self.currency_amount is None:
            raise ValueError("currency_amount is required when currency is set")
        if self.currency_amount is not None:
            object.__setattr__(
                self, "currency_amount", _ensure_decimal(self.currency_amount, "currency_amount")
            )


@dataclass(frozen=True)
class TransferRecord:
    """Persisted transfer record from storage."""
    key: int
    date: dt.date
    from_account: str
    to_account: str
    amount: Decimal
    notes: str | None
    currency: str | None
    currency_amount: Decimal | None
    time_stamp: str
