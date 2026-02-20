"""Client orchestration layer for HomeBudget."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar
import datetime as dt
from decimal import Decimal
import json
import os

from homebudget.models import (
    BatchResult,
    BatchOperation,
    BatchOperationResult,
    ExpenseDTO,
    ExpenseRecord,
    IncomeDTO,
    IncomeRecord,
    TransferDTO,
    TransferRecord,
)
from homebudget.persistence import PersistenceBackend
from homebudget.repository import Repository
from homebudget.sync import SyncUpdateManager
from homebudget.ui_control import HomeBudgetUIController

T = TypeVar("T")

ALLOWED_BATCH_RESOURCES = {"expense", "income", "transfer"}
ALLOWED_BATCH_OPERATIONS = {"add", "update", "delete"}


class HomeBudgetClient:
    """Coordinate repository operations and sync updates."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        enable_sync: bool = True,
        enable_ui_control: bool = False,
        repository: PersistenceBackend | None = None,
    ) -> None:
        """Initialize the client with a repository backend.
        
        Args:
            db_path: Path to the HomeBudget database
            enable_sync: Whether to create SyncUpdate records for changes
            enable_ui_control: Whether to close/reopen UI during database operations
            repository: Optional custom persistence backend
        """
        self.enable_sync = enable_sync
        self.enable_ui_control = enable_ui_control
        self.db_path = self._resolve_db_path(db_path, repository)
        self.repository = repository or Repository(self.db_path)

    def __enter__(self) -> "HomeBudgetClient":
        """Open the repository connection."""
        self.repository.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Close the repository connection."""
        self.close()

    def close(self) -> None:
        """Close the repository connection."""
        self.repository.close()

    def _resolve_db_path(
        self,
        db_path: str | Path | None,
        repository: PersistenceBackend | None,
    ) -> Path:
        """Resolve the database path from arguments or config."""
        if repository is not None and db_path is None:
            return Path("")
        if db_path is not None:
            return Path(db_path)
        config_path = (
            Path(os.environ["USERPROFILE"]) / "OneDrive" / "Documents" / "HomeBudgetData" / "hb-config.json"
        )
        if not config_path.exists():
            raise ValueError("db_path is required when config file is missing")
        with config_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        resolved = payload.get("db_path")
        if not resolved:
            raise ValueError("db_path is missing in config file")
        return Path(resolved)

    def _run_transaction(self, action: Callable[[], T]) -> T:
        """Run repository work inside a transaction.
        
        If UI control is enabled, this closes the HomeBudget UI before the transaction,
        executes the transaction, and reopens the UI after completion.
        
        Args:
            action: Callable that performs the database operation
            
        Returns:
            Result from the action callable
            
        Raises:
            Any exception raised by the action or transaction management
        """
        def execute_transaction() -> T:
            self.repository.begin_transaction()
            try:
                result = action()
                self.repository.commit()
                return result
            except Exception:
                self.repository.rollback()
                raise
        
        if not self.enable_ui_control:
            return execute_transaction()
        
        # Use UI control: close UI, execute transaction, reopen UI
        # Close UI
        close_success, close_msg = HomeBudgetUIController.close(verify=True)
        if not close_success:
            raise RuntimeError(f"Failed to close UI: {close_msg}")
        
        try:
            # Execute database operation and capture result
            result = execute_transaction()
            return result
        finally:
            # Always reopen UI, even if transaction failed
            open_success, open_msg = HomeBudgetUIController.open(verify=True)
            if not open_success:
                # Log warning but don't raise - UI may reopen on its own
                import sys
                print(f"[WARN] Failed to reopen UI: {open_msg}", file=sys.stderr)

    def _get_sync_manager(self) -> SyncUpdateManager | None:
        """Get sync manager if sync is enabled, else None."""
        if not self.enable_sync:
            return None
        return SyncUpdateManager(self.repository.connection)

    def _collect_changed_fields(
        self,
        amount: Decimal | str | int | float | None = None,
        notes: str | None = None,
        currency: str | None = None,
        currency_amount: Decimal | str | int | float | None = None,
    ) -> dict[str, object]:
        """Collect which fields were provided for update."""
        changed = {}
        if amount is not None:
            changed["amount"] = amount
        if notes is not None:
            changed["notes"] = notes
        if currency is not None:
            changed["currency"] = currency
        if currency_amount is not None:
            changed["currency_amount"] = currency_amount
        return changed

    def add_expense(self, expense: ExpenseDTO) -> ExpenseRecord:
        """Add an expense and return the created record."""

        def action() -> ExpenseRecord:
            record = self.repository.insert_expense(expense)
            manager = self._get_sync_manager()
            if manager:
                manager.create_sync_record(record)
            return record

        return self._run_transaction(action)

    def get_expense(self, key: int) -> ExpenseRecord:
        """Get a single expense by key."""
        return self.repository.get_expense(key)

    def list_expenses(
        self,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
    ) -> list[ExpenseRecord]:
        """List expenses within an optional date range."""
        return self.repository.list_expenses(start_date=start_date, end_date=end_date)

    def update_expense(
        self,
        key: int,
        amount: Decimal | str | int | float | None = None,
        notes: str | None = None,
        currency: str | None = None,
        currency_amount: Decimal | str | int | float | None = None,
        exchange_rate: Decimal | str | int | float | None = None,
    ) -> ExpenseRecord:
        """Update an expense and return the latest record.
        
        Creates a separate SyncUpdate entry for each changed field to match
        native app behavior where each field change generates its own sync event.
        """

        amount, currency, currency_amount = self._normalize_forex_inputs(
            amount=amount,
            currency=currency,
            currency_amount=currency_amount,
            exchange_rate=exchange_rate,
            label="Expense update",
            allow_empty=notes is not None,
        )

        def action() -> ExpenseRecord:
            record = self.repository.update_expense(
                key=key,
                amount=amount,
                notes=notes,
                currency=currency,
                currency_amount=currency_amount,
            )
            manager = self._get_sync_manager()
            if manager:
                changed = self._collect_changed_fields(amount, notes, currency, currency_amount)
                manager.create_updates_for_changes(record, "UpdateExpense", changed)
            return record

        return self._run_transaction(action)

    def delete_expense(self, key: int) -> None:
        """Delete an expense and record the sync update."""

        def action() -> None:
            record = self.repository.get_expense(key)
            self.repository.delete_expense(key)
            manager = self._get_sync_manager()
            if manager:
                manager.create_sync_record(record, "DeleteExpense")
            return None

        self._run_transaction(action)

    def add_income(self, income: IncomeDTO) -> IncomeRecord:
        """Add an income record and return the created record."""

        def action() -> IncomeRecord:
            record = self.repository.insert_income(income)
            manager = self._get_sync_manager()
            if manager:
                manager.create_sync_record(record)
            return record

        return self._run_transaction(action)

    def get_income(self, key: int) -> IncomeRecord:
        """Get a single income record by key."""
        return self.repository.get_income(key)

    def list_incomes(
        self,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
    ) -> list[IncomeRecord]:
        """List income records within an optional date range."""
        return self.repository.list_incomes(start_date=start_date, end_date=end_date)

    def update_income(
        self,
        key: int,
        amount: Decimal | str | int | float | None = None,
        notes: str | None = None,
        currency: str | None = None,
        currency_amount: Decimal | str | int | float | None = None,
        exchange_rate: Decimal | str | int | float | None = None,
    ) -> IncomeRecord:
        """Update an income record and return the latest record.
        
        Creates a separate SyncUpdate entry for each changed field to match
        native app behavior where each field change generates its own sync event.
        """

        amount, currency, currency_amount = self._normalize_forex_inputs(
            amount=amount,
            currency=currency,
            currency_amount=currency_amount,
            exchange_rate=exchange_rate,
            label="Income update",
            allow_empty=notes is not None,
        )

        def action() -> IncomeRecord:
            record = self.repository.update_income(
                key=key,
                amount=amount,
                notes=notes,
                currency=currency,
                currency_amount=currency_amount,
            )
            manager = self._get_sync_manager()
            if manager:
                changed = self._collect_changed_fields(amount, notes, currency, currency_amount)
                manager.create_updates_for_changes(record, "UpdateIncome", changed)
            return record

        return self._run_transaction(action)

    def delete_income(self, key: int) -> None:
        """Delete an income record and record the sync update."""

        def action() -> None:
            record = self.repository.get_income(key)
            self.repository.delete_income(key)
            manager = self._get_sync_manager()
            if manager:
                manager.create_sync_record(record, "DeleteIncome")
            return None

        self._run_transaction(action)

    def add_transfer(self, transfer: TransferDTO) -> TransferRecord:
        """Add a transfer and return the created record."""

        def action() -> TransferRecord:
            record = self.repository.insert_transfer(transfer)
            manager = self._get_sync_manager()
            if manager:
                manager.create_sync_record(record)
            return record

        return self._run_transaction(action)

    def get_transfer(self, key: int) -> TransferRecord:
        """Get a single transfer by key."""
        return self.repository.get_transfer(key)

    def list_transfers(
        self,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
    ) -> list[TransferRecord]:
        """List transfers within an optional date range."""
        return self.repository.list_transfers(start_date=start_date, end_date=end_date)

    def update_transfer(
        self,
        key: int,
        amount: Decimal | str | int | float | None = None,
        notes: str | None = None,
        currency: str | None = None,
        currency_amount: Decimal | str | int | float | None = None,
        exchange_rate: Decimal | str | int | float | None = None,
    ) -> TransferRecord:
        """Update a transfer and return the latest record.
        
        Creates a separate SyncUpdate entry for each changed field to match
        native app behavior where each field change generates its own sync event.
        """

        amount, currency, currency_amount = self._normalize_forex_inputs(
            amount=amount,
            currency=currency,
            currency_amount=currency_amount,
            exchange_rate=exchange_rate,
            label="Transfer update",
            allow_empty=notes is not None,
        )

        def action() -> TransferRecord:
            record = self.repository.update_transfer(
                key=key,
                amount=amount,
                notes=notes,
                currency=currency,
                currency_amount=currency_amount,
            )
            manager = self._get_sync_manager()
            if manager:
                changed = self._collect_changed_fields(amount, notes, currency, currency_amount)
                manager.create_updates_for_changes(record, "UpdateTransfer", changed)
            return record

        return self._run_transaction(action)

    def delete_transfer(self, key: int) -> None:
        """Delete a transfer and record the sync update."""

        def action() -> None:
            record = self.repository.get_transfer(key)
            self.repository.delete_transfer(key)
            manager = self._get_sync_manager()
            if manager:
                manager.create_sync_record(record, "DeleteTransfer")
            return None

        self._run_transaction(action)

    def _normalize_forex_inputs(
        self,
        *,
        amount: Decimal | str | int | float | None,
        currency: str | None,
        currency_amount: Decimal | str | int | float | None,
        exchange_rate: Decimal | str | int | float | None,
        label: str,
        allow_empty: bool,
    ) -> tuple[Decimal | None, str | None, Decimal | None]:
        """Normalize forex inputs for updates.

        Rules:
        - amount and currency_amount are mutually exclusive.
        - currency_amount requires exchange_rate and currency.
        - amount defaults currency_amount to amount.
        """
        if amount is not None and currency_amount is not None:
            if exchange_rate is not None:
                raise ValueError(
                    f"{label}: provide amount or currency_amount with exchange_rate, not both"
                )
            amount_dec = Decimal(str(amount))
            currency_amount_dec = Decimal(str(currency_amount))
            if amount_dec != currency_amount_dec:
                raise ValueError(
                    f"{label}: provide amount or currency_amount with exchange_rate, not both"
                )
            currency_amount = amount_dec
            amount = amount_dec

        if currency_amount is not None:
            if exchange_rate is None:
                raise ValueError(f"{label}: exchange_rate is required with currency_amount")
            if currency is None or not currency.strip():
                raise ValueError(f"{label}: currency is required with currency_amount")
            amount = Decimal(str(currency_amount)) * Decimal(str(exchange_rate))

        if amount is None and currency_amount is None and not allow_empty:
            raise ValueError(f"{label}: amount or currency_amount is required")

        if amount is not None and currency_amount is None:
            currency_amount = amount

        if amount is None and currency_amount is None and (currency or exchange_rate):
            raise ValueError(
                f"{label}: amount or currency_amount is required when setting currency fields"
            )

        return amount, currency, currency_amount

    @staticmethod
    def _parse_date(value: dt.date | str | None, label: str) -> dt.date:
        """Parse a date value for batch operations."""
        if value is None:
            raise ValueError(f"{label} is required")
        if isinstance(value, dt.date):
            return value
        try:
            return dt.date.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError(f"{label} must be YYYY-MM-DD") from exc

    @staticmethod
    def _parse_decimal(value: object | None, label: str) -> Decimal | None:
        """Parse a decimal value for batch operations."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except Exception as exc:
            raise ValueError(f"{label} must be a decimal") from exc

    @staticmethod
    def _parse_key(value: object | None, label: str) -> int:
        """Parse a key value for batch operations."""
        if value is None:
            raise ValueError(f"{label} is required")
        try:
            return int(value)
        except Exception as exc:
            raise ValueError(f"{label} must be an integer") from exc

    def _resolve_batch_forex_add(
        self,
        *,
        amount: Decimal | None,
        currency: str | None,
        currency_amount: Decimal | None,
        exchange_rate: Decimal | None,
        label: str,
    ) -> tuple[Decimal, str | None, Decimal | None]:
        """Resolve forex inputs for batch add operations."""
        if amount is not None and currency_amount is not None:
            raise ValueError(
                f"{label}: provide amount or currency_amount with exchange_rate, not both"
            )

        if currency_amount is not None:
            if exchange_rate is None:
                raise ValueError(f"{label}: exchange_rate is required with currency_amount")
            if currency is None or not currency.strip():
                raise ValueError(f"{label}: currency is required with currency_amount")
            amount = currency_amount * exchange_rate

        if amount is None and currency_amount is None:
            raise ValueError(f"{label}: amount or currency_amount is required")

        if amount is not None and currency_amount is None:
            currency_amount = amount

        return amount, currency, currency_amount

    def _build_expense_dto(self, parameters: dict[str, object]) -> ExpenseDTO:
        """Build an ExpenseDTO from batch parameters."""
        date = self._parse_date(parameters.get("date"), "Expense date")
        amount = self._parse_decimal(parameters.get("amount"), "Expense amount")
        currency_amount = self._parse_decimal(
            parameters.get("currency_amount"), "Expense currency_amount"
        )
        exchange_rate = self._parse_decimal(
            parameters.get("exchange_rate"), "Expense exchange_rate"
        )
        amount, currency, currency_amount = self._resolve_batch_forex_add(
            amount=amount,
            currency=str(parameters.get("currency")) if parameters.get("currency") else None,
            currency_amount=currency_amount,
            exchange_rate=exchange_rate,
            label="Expense add",
        )
        return ExpenseDTO(
            date=date,
            category=str(parameters.get("category") or ""),
            subcategory=str(parameters.get("subcategory") or ""),
            amount=amount,
            account=str(parameters.get("account") or ""),
            notes=str(parameters.get("notes")) if parameters.get("notes") is not None else None,
            currency=currency,
            currency_amount=currency_amount,
        )

    def _build_income_dto(self, parameters: dict[str, object]) -> IncomeDTO:
        """Build an IncomeDTO from batch parameters."""
        date = self._parse_date(parameters.get("date"), "Income date")
        amount = self._parse_decimal(parameters.get("amount"), "Income amount")
        currency_amount = self._parse_decimal(
            parameters.get("currency_amount"), "Income currency_amount"
        )
        exchange_rate = self._parse_decimal(
            parameters.get("exchange_rate"), "Income exchange_rate"
        )
        amount, currency, currency_amount = self._resolve_batch_forex_add(
            amount=amount,
            currency=str(parameters.get("currency")) if parameters.get("currency") else None,
            currency_amount=currency_amount,
            exchange_rate=exchange_rate,
            label="Income add",
        )
        return IncomeDTO(
            date=date,
            name=str(parameters.get("name") or ""),
            amount=amount,
            account=str(parameters.get("account") or ""),
            notes=str(parameters.get("notes")) if parameters.get("notes") is not None else None,
            currency=currency,
            currency_amount=currency_amount,
        )

    def _build_transfer_dto(self, parameters: dict[str, object]) -> TransferDTO:
        """Build a TransferDTO from batch parameters."""
        date = self._parse_date(parameters.get("date"), "Transfer date")
        amount = self._parse_decimal(parameters.get("amount"), "Transfer amount")
        currency_amount = self._parse_decimal(
            parameters.get("currency_amount"), "Transfer currency_amount"
        )
        exchange_rate = self._parse_decimal(
            parameters.get("exchange_rate"), "Transfer exchange_rate"
        )
        amount, currency, currency_amount = self._resolve_batch_forex_add(
            amount=amount,
            currency=str(parameters.get("currency")) if parameters.get("currency") else None,
            currency_amount=currency_amount,
            exchange_rate=exchange_rate,
            label="Transfer add",
        )
        return TransferDTO(
            date=date,
            from_account=str(parameters.get("from_account") or ""),
            to_account=str(parameters.get("to_account") or ""),
            amount=amount,
            notes=str(parameters.get("notes")) if parameters.get("notes") is not None else None,
            currency=currency,
            currency_amount=currency_amount,
        )

    def _apply_batch_operation(
        self, operation: BatchOperation
    ) -> tuple[
        ExpenseRecord | IncomeRecord | TransferRecord,
        str,
        dict[str, object] | None,
    ]:
        """Execute a single batch operation and return sync details."""
        resource = operation.resource.strip().lower()
        action = operation.operation.strip().lower()
        parameters = operation.parameters

        if resource not in ALLOWED_BATCH_RESOURCES:
            raise ValueError(f"Unsupported batch resource: {operation.resource}")
        if action not in ALLOWED_BATCH_OPERATIONS:
            raise ValueError(f"Unsupported batch operation: {operation.operation}")

        if resource == "expense":
            if action == "add":
                dto = self._build_expense_dto(parameters)
                record = self.repository.insert_expense(dto)
                return record, "AddExpense", None
            if action == "update":
                key = self._parse_key(parameters.get("key"), "Expense key")
                amount = self._parse_decimal(parameters.get("amount"), "Expense amount")
                currency_amount = self._parse_decimal(
                    parameters.get("currency_amount"), "Expense currency_amount"
                )
                exchange_rate = self._parse_decimal(
                    parameters.get("exchange_rate"), "Expense exchange_rate"
                )
                currency = parameters.get("currency")
                notes = parameters.get("notes")
                if amount is None and notes is None and currency is None and currency_amount is None:
                    raise ValueError("Expense update requires at least one field")
                normalized_currency = str(currency) if currency is not None else None
                normalized_notes = str(notes) if notes is not None else None
                amount, currency, currency_amount = self._normalize_forex_inputs(
                    amount=amount,
                    currency=normalized_currency,
                    currency_amount=currency_amount,
                    exchange_rate=exchange_rate,
                    label="Expense update",
                    allow_empty=notes is not None,
                )
                record = self.repository.update_expense(
                    key=key,
                    amount=amount,
                    notes=normalized_notes,
                    currency=normalized_currency,
                    currency_amount=currency_amount,
                )
                changed = self._collect_changed_fields(
                    amount, normalized_notes, normalized_currency, currency_amount
                )
                return record, "UpdateExpense", changed
            key = self._parse_key(parameters.get("key"), "Expense key")
            record = self.repository.get_expense(key)
            self.repository.delete_expense(key)
            return record, "DeleteExpense", None

        if resource == "income":
            if action == "add":
                dto = self._build_income_dto(parameters)
                record = self.repository.insert_income(dto)
                return record, "AddIncome", None
            if action == "update":
                key = self._parse_key(parameters.get("key"), "Income key")
                amount = self._parse_decimal(parameters.get("amount"), "Income amount")
                currency_amount = self._parse_decimal(
                    parameters.get("currency_amount"), "Income currency_amount"
                )
                exchange_rate = self._parse_decimal(
                    parameters.get("exchange_rate"), "Income exchange_rate"
                )
                currency = parameters.get("currency")
                notes = parameters.get("notes")
                if amount is None and notes is None and currency is None and currency_amount is None:
                    raise ValueError("Income update requires at least one field")
                normalized_currency = str(currency) if currency is not None else None
                normalized_notes = str(notes) if notes is not None else None
                amount, currency, currency_amount = self._normalize_forex_inputs(
                    amount=amount,
                    currency=normalized_currency,
                    currency_amount=currency_amount,
                    exchange_rate=exchange_rate,
                    label="Income update",
                    allow_empty=notes is not None,
                )
                record = self.repository.update_income(
                    key=key,
                    amount=amount,
                    notes=normalized_notes,
                    currency=normalized_currency,
                    currency_amount=currency_amount,
                )
                changed = self._collect_changed_fields(
                    amount, normalized_notes, normalized_currency, currency_amount
                )
                return record, "UpdateIncome", changed
            key = self._parse_key(parameters.get("key"), "Income key")
            record = self.repository.get_income(key)
            self.repository.delete_income(key)
            return record, "DeleteIncome", None

        if action == "add":
            dto = self._build_transfer_dto(parameters)
            record = self.repository.insert_transfer(dto)
            return record, "AddTransfer", None
        if action == "update":
            key = self._parse_key(parameters.get("key"), "Transfer key")
            amount = self._parse_decimal(parameters.get("amount"), "Transfer amount")
            currency_amount = self._parse_decimal(
                parameters.get("currency_amount"), "Transfer currency_amount"
            )
            exchange_rate = self._parse_decimal(
                parameters.get("exchange_rate"), "Transfer exchange_rate"
            )
            currency = parameters.get("currency")
            notes = parameters.get("notes")
            if amount is None and notes is None and currency is None and currency_amount is None:
                raise ValueError("Transfer update requires at least one field")
            normalized_currency = str(currency) if currency is not None else None
            normalized_notes = str(notes) if notes is not None else None
            amount, currency, currency_amount = self._normalize_forex_inputs(
                amount=amount,
                currency=normalized_currency,
                currency_amount=currency_amount,
                exchange_rate=exchange_rate,
                label="Transfer update",
                allow_empty=notes is not None,
            )
            record = self.repository.update_transfer(
                key=key,
                amount=amount,
                notes=normalized_notes,
                currency=normalized_currency,
                currency_amount=currency_amount,
            )
            changed = self._collect_changed_fields(
                amount, normalized_notes, normalized_currency, currency_amount
            )
            return record, "UpdateTransfer", changed
        key = self._parse_key(parameters.get("key"), "Transfer key")
        record = self.repository.get_transfer(key)
        self.repository.delete_transfer(key)
        return record, "DeleteTransfer", None

    def batch(
        self,
        operations: list[BatchOperation],
        continue_on_error: bool = True,
    ) -> BatchOperationResult:
        """Run mixed batch operations across resources.

        Args:
            operations: Batch operations to execute in order
            continue_on_error: If True, continue processing after errors and collect
                failures. If False, raise on the first error.

        Returns:
            BatchOperationResult with successful records and any failures

        Raises:
            Exception: If continue_on_error is False and any operation fails
        """
        successful: list[ExpenseRecord | IncomeRecord | TransferRecord] = []
        failed: list[tuple[BatchOperation, Exception]] = []
        sync_actions: list[tuple[ExpenseRecord | IncomeRecord | TransferRecord, str, dict[str, object] | None]] = []

        def action() -> BatchOperationResult:
            original_sync_setting = self.enable_sync
            self.enable_sync = False

            try:
                for operation in operations:
                    try:
                        record, sync_operation, changed_fields = self._apply_batch_operation(
                            operation
                        )
                        successful.append(record)
                        sync_actions.append((record, sync_operation, changed_fields))
                    except Exception as exc:
                        if not continue_on_error:
                            raise
                        failed.append((operation, exc))

                self.enable_sync = original_sync_setting
                if self.enable_sync:
                    manager = self._get_sync_manager()
                    if manager:
                        for record, sync_operation, changed_fields in sync_actions:
                            if sync_operation.startswith("Update") and changed_fields:
                                manager.create_updates_for_changes(
                                    record, sync_operation, changed_fields
                                )
                            else:
                                manager.create_sync_record(record, sync_operation)

                return BatchOperationResult(successful=successful, failed=failed)
            finally:
                self.enable_sync = original_sync_setting

        return self._run_transaction(action)
    def add_expenses_batch(
        self,
        expenses: list[ExpenseDTO],
        continue_on_error: bool = True,
    ) -> BatchResult:
        """Add multiple expenses in a batch operation.
        
        Batch implementation disables sync during individual inserts and performs
        a single sync operation after all successful inserts complete.
        
        Args:
            expenses: List of validated expense DTOs
            continue_on_error: If True, continue processing after errors and collect
                              failures. If False, raise on first error.
        
        Returns:
            BatchResult with successful records and any failures
            
        Raises:
            Exception: If continue_on_error is False and any expense fails
        """
        successful: list[ExpenseRecord] = []
        failed: list[tuple[ExpenseDTO, Exception]] = []

        def action() -> BatchResult:
            # Disable sync temporarily
            original_sync_setting = self.enable_sync
            self.enable_sync = False

            try:
                # Process each expense
                for expense in expenses:
                    try:
                        record = self.repository.insert_expense(expense)
                        successful.append(record)
                    except Exception as e:
                        if not continue_on_error:
                            raise
                        failed.append((expense, e))

                # Re-enable sync and create sync entries for successful records
                self.enable_sync = original_sync_setting
                if self.enable_sync:
                    manager = self._get_sync_manager()
                    if manager:
                        for record in successful:
                            manager.create_sync_record(record)

                return BatchResult(successful=successful, failed=failed)
            finally:
                # Always restore original sync setting
                self.enable_sync = original_sync_setting

        return self._run_transaction(action)

    def add_incomes_batch(
        self,
        incomes: list[IncomeDTO],
        continue_on_error: bool = True,
    ) -> BatchResult:
        """Add multiple income records in a batch operation.
        
        Batch implementation disables sync during individual inserts and performs
        a single sync operation after all successful inserts complete.
        
        Args:
            incomes: List of validated income DTOs
            continue_on_error: If True, continue processing after errors and collect
                              failures. If False, raise on first error.
        
        Returns:
            BatchResult with successful records and any failures
            
        Raises:
            Exception: If continue_on_error is False and any income fails
        """
        successful: list[IncomeRecord] = []
        failed: list[tuple[IncomeDTO, Exception]] = []

        def action() -> BatchResult:
            # Disable sync temporarily
            original_sync_setting = self.enable_sync
            self.enable_sync = False

            try:
                # Process each income
                for income in incomes:
                    try:
                        record = self.repository.insert_income(income)
                        successful.append(record)
                    except Exception as e:
                        if not continue_on_error:
                            raise
                        failed.append((income, e))

                # Re-enable sync and create sync entries for successful records
                self.enable_sync = original_sync_setting
                if self.enable_sync:
                    manager = self._get_sync_manager()
                    if manager:
                        for record in successful:
                            manager.create_sync_record(record)

                return BatchResult(successful=successful, failed=failed)
            finally:
                # Always restore original sync setting
                self.enable_sync = original_sync_setting

        return self._run_transaction(action)

    def add_transfers_batch(
        self,
        transfers: list[TransferDTO],
        continue_on_error: bool = True,
    ) -> BatchResult:
        """Add multiple transfers in a batch operation.
        
        Batch implementation disables sync during individual inserts and performs
        a single sync operation after all successful inserts complete.
        
        Args:
            transfers: List of validated transfer DTOs
            continue_on_error: If True, continue processing after errors and collect
                              failures. If False, raise on first error.
        
        Returns:
            BatchResult with successful records and any failures
            
        Raises:
            Exception: If continue_on_error is False and any transfer fails
        """
        successful: list[TransferRecord] = []
        failed: list[tuple[TransferDTO, Exception]] = []

        def action() -> BatchResult:
            # Disable sync temporarily
            original_sync_setting = self.enable_sync
            self.enable_sync = False

            try:
                # Process each transfer
                for transfer in transfers:
                    try:
                        record = self.repository.insert_transfer(transfer)
                        successful.append(record)
                    except Exception as e:
                        if not continue_on_error:
                            raise
                        failed.append((transfer, e))

                # Re-enable sync and create sync entries for successful records
                self.enable_sync = original_sync_setting
                if self.enable_sync:
                    manager = self._get_sync_manager()
                    if manager:
                        for record in successful:
                            manager.create_sync_record(record)

                return BatchResult(successful=successful, failed=failed)
            finally:
                # Always restore original sync setting
                self.enable_sync = original_sync_setting

        return self._run_transaction(action)
