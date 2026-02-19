"""Public HomeBudget package exports."""

from __future__ import annotations

from homebudget.__version__ import __version__
from homebudget.client import HomeBudgetClient
from homebudget.exceptions import DuplicateError, NotFoundError
from homebudget.models import (
    ExpenseDTO,
    ExpenseRecord,
    IncomeDTO,
    IncomeRecord,
    TransferDTO,
    TransferRecord,
)
from homebudget.persistence import PersistenceBackend
from homebudget.repository import Repository

__all__ = [
    "__version__",
    "HomeBudgetClient",
    "DuplicateError",
    "NotFoundError",
    "ExpenseDTO",
    "ExpenseRecord",
    "IncomeDTO",
    "IncomeRecord",
    "TransferDTO",
    "TransferRecord",
    "PersistenceBackend",
    "Repository",
]
