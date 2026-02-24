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


ALLOWED_DECIMAL_PLACES = {0, 2}


def _ensure_decimal_places(value: int | None, field_name: str) -> int | None:
    """Validate decimal places for currency rounding."""
    if value is None:
        return None
    if value not in ALLOWED_DECIMAL_PLACES:
        raise ValueError(f"{field_name} must be 0 or 2")
    return value


class BaseTransactionDTO:
    """Shared validation behavior for transaction DTOs."""

    date: dt.date
    amount: Decimal
    currency: str | None
    currency_amount: Decimal | None
    amount_decimal_places: int | None
    currency_amount_decimal_places: int | None

    def _validate_base_fields(self) -> None:
        object.__setattr__(self, "date", _ensure_date(self.date))
        # For TransferDTO, amount can be None (will be inferred)
        if self.amount is not None:
            object.__setattr__(self, "amount", _ensure_decimal(self.amount, "Amount"))
        object.__setattr__(
            self,
            "amount_decimal_places",
            _ensure_decimal_places(self.amount_decimal_places, "amount_decimal_places"),
        )
        object.__setattr__(
            self,
            "currency_amount_decimal_places",
            _ensure_decimal_places(
                self.currency_amount_decimal_places, "currency_amount_decimal_places"
            ),
        )
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
                self,
                "currency_amount",
                _ensure_decimal(self.currency_amount, "currency_amount"),
            )


@dataclass(frozen=True)
class ExpenseDTO(BaseTransactionDTO):
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
    amount_decimal_places: int | None = None
    currency_amount_decimal_places: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", _ensure_non_empty(self.category, "Category"))
        object.__setattr__(
            self, "subcategory", _ensure_non_empty(self.subcategory, "Subcategory")
        )
        object.__setattr__(self, "account", _ensure_non_empty(self.account, "Account"))
        self._validate_base_fields()


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
class IncomeDTO(BaseTransactionDTO):
    """Validated income input for persistence."""
    date: dt.date
    name: str
    amount: Decimal
    account: str
    notes: str | None = None
    currency: str | None = None
    currency_amount: Decimal | None = None
    amount_decimal_places: int | None = None
    currency_amount_decimal_places: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _ensure_non_empty(self.name, "Name"))
        object.__setattr__(self, "account", _ensure_non_empty(self.account, "Account"))
        self._validate_base_fields()


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
class TransferDTO(BaseTransactionDTO):
    """Validated transfer input for persistence."""
    date: dt.date
    from_account: str
    to_account: str
    amount: Decimal | None = None
    notes: str | None = None
    currency: str | None = None
    currency_amount: Decimal | None = None
    amount_decimal_places: int | None = None
    currency_amount_decimal_places: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "from_account", _ensure_non_empty(self.from_account, "From account")
        )
        object.__setattr__(
            self, "to_account", _ensure_non_empty(self.to_account, "To account")
        )
        if self.from_account == self.to_account:
            raise ValueError("From account and to account must differ")
        self._validate_base_fields()


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
    time_stamp: str | None


@dataclass(frozen=True)
class BatchOperation:
    """Single batch operation for mixed resource workflows."""
    resource: str
    operation: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class BatchOperationResult:
    """Result of a mixed batch operation run."""
    successful: list[ExpenseRecord | IncomeRecord | TransferRecord]
    failed: list[tuple[BatchOperation, Exception]]


@dataclass(frozen=True)
class BatchResult:
    """Result of a batch operation."""
    successful: list[ExpenseRecord | IncomeRecord | TransferRecord]
    failed: list[tuple[ExpenseDTO | IncomeDTO | TransferDTO, Exception]]
    operation_id: str | None = None


@dataclass(frozen=True)
class BalanceRecord:
    """Account balance at a given query date.
    
    Represents the calculated balance of an account at a specific date,
    based on the most recent reconcile balance and subsequent transactions.
    
    Attributes:
        accountKey: Internal database key for the account
        accountName: Display name of the account
        queryDate: Date for which the balance was calculated
        balanceAmount: Calculated balance at the query date
        reconcileDate: Date of the most recent reconcile balance
        reconcileAmount: Amount of the most recent reconcile balance
    """
    accountKey: int
    accountName: str
    queryDate: dt.date
    balanceAmount: Decimal
    reconcileDate: dt.date
    reconcileAmount: Decimal


@dataclass(frozen=True)
class AccountRecord:
    """Reference record for an account with balance info.
    
    Represents a summary of an account including its type, balance, and currency.
    Used for displaying account lists and reference data.
    
    Attributes:
        key: Internal database key for the account
        name: Display name of the account
        accountType: Type of account (Checking, Savings, Credit Card, etc.)
        balance: Current account balance
        currency: Currency code for the account
    """
    key: int
    name: str
    accountType: str
    balance: Decimal
    currency: str


@dataclass(frozen=True)
class CategoryRecord:
    """Reference record for an expense category.
    
    Represents a spend category for organizing expenses and budgets.
    Ordered by sequence number for consistent display order.
    
    Attributes:
        key: Internal database key for the category
        name: Display name of the category
        seqNum: Sequence number for display ordering
    """
    key: int
    name: str
    seqNum: int


@dataclass(frozen=True)
class SubcategoryRecord:
    """Reference record for a subcategory with parent category context.
    
    Represents a subcategory under a parent category for detailed expense tracking.
    Includes parent category information for context.
    
    Attributes:
        key: Internal database key for the subcategory
        categoryKey: Internal database key for the parent category
        categoryName: Display name of the parent category
        name: Display name of the subcategory
        seqNum: Sequence number for display ordering within the category
    """
    key: int
    categoryKey: int
    categoryName: str
    name: str
    seqNum: int
