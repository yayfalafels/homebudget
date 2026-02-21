"""Client orchestration layer for HomeBudget."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar
import datetime as dt
from decimal import Decimal
import json
import logging
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
from homebudget.forex import ForexRateManager, REF_CURRENCY
from homebudget.exceptions import NotFoundError

T = TypeVar("T")

# Configure logging
logger = logging.getLogger(__name__)
log_level = os.environ.get('LOGGING_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
    logger.addHandler(handler)

ALLOWED_BATCH_RESOURCES = {"expense", "income", "transfer"}
ALLOWED_BATCH_OPERATIONS = {"add", "update", "delete"}
DEFAULT_FOREX_TTL_HOURS = 1
DEFAULT_FOREX_CACHE_NAME = "forex-rates.json"
HIGH_VALUE_RATE_THRESHOLD = Decimal("100")
HIGH_VALUE_DECIMAL_PLACES = 0
STANDARD_DECIMAL_PLACES = 2


class HomeBudgetClient:
    """Coordinate repository operations and sync updates."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        enable_sync: bool = True,
        enable_ui_control: bool = False,
        repository: PersistenceBackend | None = None,
        enable_forex_rates: bool = True,
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
        self.config = self._load_config()
        self.enable_forex_rates = enable_forex_rates
        self._forex_manager = None
        if self.enable_forex_rates:
            self._forex_manager = ForexRateManager(
                config=self.config.get("forex", {"cache_ttl_hours": DEFAULT_FOREX_TTL_HOURS}),
                cache_path=self._derive_cache_path(),
            )

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

    def _load_config(self) -> dict:
        """Load config file if present, else return empty config."""
        config_path = (
            Path(os.environ.get("USERPROFILE", ""))
            / "OneDrive"
            / "Documents"
            / "HomeBudgetData"
            / "hb-config.json"
        )
        if not config_path.exists():
            return {}
        with config_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            return {}
        return payload

    def _derive_cache_path(self) -> Path:
        """Derive the forex cache path in dedicated Forex directory."""
        if not self.db_path:
            return Path(DEFAULT_FOREX_CACHE_NAME)
        # Place cache in Forex subdirectory: */HomeBudgetData/Forex/forex-rates.json
        data_dir = Path(self.db_path).parent
        forex_dir = data_dir.parent / "Forex"
        forex_dir.mkdir(parents=True, exist_ok=True)
        return forex_dir / DEFAULT_FOREX_CACHE_NAME

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

    def _execute_create_transaction(
        self,
        insert_func: Callable[[object], T],
        record_dto: object,
        validators: list[Callable[[], None]] | None = None,
        sync_operation: str | None = None,
    ) -> T:
        """Execute a create operation with validation and sync.
        
        Base method consolidating the pattern: validate → insert → sync → return
        
        Args:
            insert_func: Repository insert method (e.g., insert_expense)
            record_dto: DTO to insert (ExpenseDTO, IncomeDTO, TransferDTO)
            validators: List of validation callables to run before insert
            sync_operation: Operation name for sync (e.g., "AddExpense")
            
        Returns:
            Created record from insert operation
        """
        # Run validators (e.g., currency validation)
        if validators:
            for validator in validators:
                validator()
        
        def action() -> T:
            record = insert_func(record_dto)
            manager = self._get_sync_manager()
            if manager and sync_operation:
                manager.create_sync_record(record, sync_operation)
            return record
        
        return self._run_transaction(action)

    def _execute_update_transaction(
        self,
        update_func: Callable,
        key: int,
        normalized_params: dict[str, object],
        sync_operation: str | None = None,
    ) -> T:
        """Execute an update operation with field tracking and sync.
        
        Base method consolidating the pattern: update → collect changes → sync → return
        
        Args:
            update_func: Repository update method (e.g., update_expense)
            key: Record key to update
            normalized_params: Normalized parameters for update (amount, currency, etc.)
            sync_operation: Operation name for sync (e.g., "UpdateExpense")
            
        Returns:
            Updated record
        """
        def action() -> T:
            record = update_func(key, **normalized_params)
            manager = self._get_sync_manager()
            if manager and sync_operation:
                changed = self._collect_changed_fields(**normalized_params)
                manager.create_updates_for_changes(record, sync_operation, changed)
            return record
        
        return self._run_transaction(action)

    def _execute_delete_transaction(
        self,
        get_func: Callable[[int], T],
        delete_func: Callable[[int], None],
        key: int,
        sync_operation: str | None = None,
    ) -> None:
        """Execute a delete operation with sync.
        
        Base method consolidating the pattern: get → delete → sync
        
        Args:
            get_func: Repository get method (e.g., get_expense)
            delete_func: Repository delete method (e.g., delete_expense)
            key: Record key to delete
            sync_operation: Operation name for sync (e.g., "DeleteExpense")
        """
        def action() -> None:
            record = get_func(key)
            delete_func(key)
            manager = self._get_sync_manager()
            if manager and sync_operation:
                manager.create_sync_record(record, sync_operation)
            return None
        
        return self._run_transaction(action)

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
        amount_decimal_places: int | None = None,
        currency_amount_decimal_places: int | None = None,
    ) -> dict[str, object]:
        """Collect which fields were provided for update.
        
        Excludes internal rounding metadata (decimal_places fields).
        """
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

    def _get_base_currency(self) -> str:
        """Get the system base currency from Settings table."""
        config_currency = self.config.get("base_currency")
        if isinstance(config_currency, str) and config_currency.strip():
            return config_currency.strip()
        row = self.repository.connection.execute(
            "SELECT currency FROM Settings LIMIT 1"
        ).fetchone()
        if row is None or not row["currency"]:
            raise ValueError("Base currency not configured")
        return row["currency"]

    def _get_account_currency(self, account_name: str) -> str:
        """Get the currency for an account and enforce non null currency."""
        row = self.repository.connection.execute(
            "SELECT currency FROM Account WHERE name = ?",
            (account_name,),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Account {account_name} not found")
        if not row["currency"]:
            raise ValueError(f"Account {account_name} has no currency defined")
        return row["currency"]

    def _get_forex_rate(self, from_currency: str) -> float:
        """Get forex rate from currency to base currency."""
        if not self._forex_manager:
            return 1.0
        base_currency = self._get_base_currency()
        return self._forex_manager.get_rate(from_currency, base_currency)

    def _get_currency_decimal_places(self, currency: str) -> int:
        """Determine decimal places for a currency using forex rates."""
        if not self._forex_manager:
            return STANDARD_DECIMAL_PLACES
        try:
            rate = self._forex_manager.get_rate(REF_CURRENCY, currency)
        except Exception:
            return STANDARD_DECIMAL_PLACES
        if Decimal(str(rate)) >= HIGH_VALUE_RATE_THRESHOLD:
            return HIGH_VALUE_DECIMAL_PLACES
        return STANDARD_DECIMAL_PLACES

    def _resolve_rounding_policy(self, currency: str | None) -> tuple[int, int]:
        """Resolve decimal places for base and currency amounts."""
        base_currency = self._get_base_currency()
        amount_decimal_places = self._get_currency_decimal_places(base_currency)
        if currency:
            currency_decimal_places = self._get_currency_decimal_places(currency)
        else:
            currency_decimal_places = amount_decimal_places
        return amount_decimal_places, currency_decimal_places

    def _apply_rounding_policy_expense(self, expense: ExpenseDTO) -> ExpenseDTO:
        """Attach rounding policy metadata to an expense DTO."""
        amount_places, currency_places = self._resolve_rounding_policy(expense.currency)
        if expense.amount_decimal_places is not None:
            amount_places = expense.amount_decimal_places
        if expense.currency_amount_decimal_places is not None:
            currency_places = expense.currency_amount_decimal_places
        return ExpenseDTO(
            date=expense.date,
            category=expense.category,
            subcategory=expense.subcategory,
            amount=expense.amount,
            account=expense.account,
            notes=expense.notes,
            payee=expense.payee,
            currency=expense.currency,
            currency_amount=expense.currency_amount,
            amount_decimal_places=amount_places,
            currency_amount_decimal_places=currency_places,
        )

    def _apply_rounding_policy_income(self, income: IncomeDTO) -> IncomeDTO:
        """Attach rounding policy metadata to an income DTO."""
        amount_places, currency_places = self._resolve_rounding_policy(income.currency)
        if income.amount_decimal_places is not None:
            amount_places = income.amount_decimal_places
        if income.currency_amount_decimal_places is not None:
            currency_places = income.currency_amount_decimal_places
        return IncomeDTO(
            date=income.date,
            name=income.name,
            amount=income.amount,
            account=income.account,
            notes=income.notes,
            currency=income.currency,
            currency_amount=income.currency_amount,
            amount_decimal_places=amount_places,
            currency_amount_decimal_places=currency_places,
        )

    def _apply_rounding_policy_transfer(self, transfer: TransferDTO) -> TransferDTO:
        """Attach rounding policy metadata to a transfer DTO."""
        amount_places, currency_places = self._resolve_rounding_policy(transfer.currency)
        if transfer.amount_decimal_places is not None:
            amount_places = transfer.amount_decimal_places
        if transfer.currency_amount_decimal_places is not None:
            currency_places = transfer.currency_amount_decimal_places
        return TransferDTO(
            date=transfer.date,
            from_account=transfer.from_account,
            to_account=transfer.to_account,
            amount=transfer.amount,
            notes=transfer.notes,
            currency=transfer.currency,
            currency_amount=transfer.currency_amount,
            amount_decimal_places=amount_places,
            currency_amount_decimal_places=currency_places,
        )

    def _validate_currency_for_account(
        self,
        account_name: str,
        transaction_currency: str | None,
        transaction_type: str,
    ) -> None:
        """Validate that transaction currency is compatible with account.
        
        Rules:
        - Cannot add base currency (SGD) to non-base currency accounts (e.g., USD accounts)
        - Can add foreign currencies (USD, EUR, etc.) to base currency accounts
        
        Args:
            account_name: Name of the account
            transaction_currency: Currency code of the transaction (None for base currency)
            transaction_type: Type of transaction ('expense', 'income', 'transfer_from', 'transfer_to')
            
        Raises:
            ValueError: If currency is incompatible with account
        """
        # If no currency specified, transaction is in base currency
        if transaction_currency is None:
            transaction_currency = self._get_base_currency()
        
        # Get account currency
        try:
            row = self.repository.connection.execute(
                "SELECT currency FROM Account WHERE name = ?",
                (account_name,),
            ).fetchone()
            if row is None:
                # Let repository handle NotFoundError
                return
            account_currency = row["currency"] or self._get_base_currency()
        except Exception:
            # If lookup fails, let it propagate as normal error
            return
        
        base_currency = self._get_base_currency()
        
        # Rule: Cannot add base currency to non-base currency accounts
        if transaction_currency == base_currency and account_currency != base_currency:
            raise ValueError(
                f"Cannot add {base_currency} (base currency) to {account_name!r} account "
                f"(which uses {account_currency}). Add a foreign currency transaction instead."
            )

    def _validate_expense_currency(self, expense: ExpenseDTO) -> None:
        """Validate expense currency compatibility with account.
        
        Pre-operation validator for expense creation/update.
        """
        self._validate_currency_for_account(
            account_name=expense.account,
            transaction_currency=expense.currency,
            transaction_type="expense",
        )

    def _validate_income_currency(self, income: IncomeDTO) -> None:
        """Validate income currency compatibility with account.
        
        Pre-operation validator for income creation/update.
        """
        self._validate_currency_for_account(
            account_name=income.account,
            transaction_currency=income.currency,
            transaction_type="income",
        )

    def _infer_currency_for_expense(self, expense: ExpenseDTO) -> ExpenseDTO:
        """Infer currency for expense on non-base accounts.
        
        For non-base currency accounts (USD, RUB, GEL, etc.), if --amount is provided
        without --currency, automatically infer:
        - currency = account currency
        - currency_amount = amount (same as what user provided)
        - This implies exchange_rate = 1.0
        
        Args:
            expense: ExpenseDTO to potentially modify
            
        Returns:
            Modified ExpenseDTO with inferred currency if applicable
        """
        logger.debug(f"_infer_currency_for_expense called: account={expense.account}, amount={expense.amount}, currency={expense.currency}, currency_amount={expense.currency_amount}")
        
        # Skip if currency or currency_amount was explicitly specified
        if expense.currency is not None or expense.currency_amount is not None:
            logger.debug("Skipping inference: currency or currency_amount already set")
            return expense

        account_currency = self._get_account_currency(expense.account)
        base_currency = self._get_base_currency()
        logger.debug(f"Account currency: {account_currency}, Base currency: {base_currency}")

        if account_currency == base_currency or not expense.amount:
            logger.debug(f"Skipping inference: account_currency == base_currency ({account_currency == base_currency}) or no amount")
            return expense

        rate = Decimal(str(self._get_forex_rate(account_currency)))
        base_amount = Decimal(str(expense.amount)) * rate
        logger.debug(f"Forex inference: rate={rate}, input_amount={expense.amount}, base_amount={base_amount}")
        
        result = ExpenseDTO(
            date=expense.date,
            category=expense.category,
            subcategory=expense.subcategory,
            amount=base_amount,
            account=expense.account,
            notes=expense.notes,
            currency=account_currency,
            currency_amount=Decimal(str(expense.amount)),
        )
        logger.debug(f"Returning modified expense: amount={result.amount}, currency={result.currency}, currency_amount={result.currency_amount}")
        return result

    def _infer_currency_for_income(self, income: IncomeDTO) -> IncomeDTO:
        """Infer currency for income on non-base accounts.
        
        For non-base currency accounts (USD, RUB, GEL, etc.), if --amount is provided
        without --currency, automatically infer:
        - currency = account currency
        - currency_amount = amount (same as what user provided)
        - This implies exchange_rate = 1.0
        
        Args:
            income: IncomeDTO to potentially modify
            
        Returns:
            Modified IncomeDTO with inferred currency if applicable
        """
        # Skip if currency or currency_amount was explicitly specified
        if income.currency is not None or income.currency_amount is not None:
            return income

        account_currency = self._get_account_currency(income.account)
        base_currency = self._get_base_currency()

        if account_currency == base_currency or not income.amount:
            return income

        rate = Decimal(str(self._get_forex_rate(account_currency)))
        base_amount = Decimal(str(income.amount)) * rate
        return IncomeDTO(
            date=income.date,
            name=income.name,
            amount=base_amount,
            account=income.account,
            notes=income.notes,
            currency=account_currency,
            currency_amount=Decimal(str(income.amount)),
        )

    def _validate_transfer_currency_constraint(self, transfer: TransferDTO) -> None:
        """Validate that currency matches from_account.
        
        By convention, transfers must have currency and currency_amount that match
        the from_account's currency. This ensures unambiguous conversion semantics.
        
        Args:
            transfer: Transfer to validate
            
        Raises:
            ValueError: If currency does not match from_account currency
        """
        if transfer.currency is None:
            # No constraint to validate if currency not specified (will be inferred)
            return
        
        from_currency = self._get_account_currency(transfer.from_account)
        
        if transfer.currency != from_currency:
            raise ValueError(
                f"Transfer currency must match from_account currency. "
                f"from_account {transfer.from_account!r} uses {from_currency}, "
                f"but transfer specifies {transfer.currency}."
            )

    def _infer_currency_for_transfer(self, transfer: TransferDTO) -> TransferDTO:
        """Infer currency, currency_amount, and amount for transfer based on accounts.
        
        Transfer table fields represent:
        - currency: from_account currency (constraint enforced)
        - currency_amount: amount in from_account currency
        - amount: amount in to_account currency
        
        User amount interpretation:
        - If base in either account: user amount is in base currency
        - If base in neither account: user amount is in from_account currency
        
        Args:
            transfer: TransferDTO to potentially modify
            
        Returns:
            Modified TransferDTO with currency, currency_amount, and amount inferred
        """
        # Skip if currency or currency_amount was explicitly specified
        if transfer.currency is not None or transfer.currency_amount is not None:
            return transfer

        from_currency = self._get_account_currency(transfer.from_account)
        to_currency = self._get_account_currency(transfer.to_account)
        base_currency = self._get_base_currency()

        if not transfer.amount:
            return transfer

        # If same currency, no inference needed
        if from_currency == to_currency:
            return transfer

        user_amount = Decimal(str(transfer.amount))

        # Currency always matches from_account
        currency = from_currency

        if from_currency == base_currency:
            # Case 1: from base -> foreign
            # User amount is in base, calculate to_amount in foreign currency
            currency_amount = user_amount  # from_amount in base
            to_rate = Decimal(str(self._get_forex_rate(to_currency)))
            to_amount = user_amount / to_rate  # to_amount in foreign
        elif to_currency == base_currency:
            # Case 2: from foreign -> base
            # User amount is in base, calculate from_amount in foreign currency
            from_rate = Decimal(str(self._get_forex_rate(from_currency)))
            currency_amount = user_amount / from_rate  # from_amount in foreign
            to_amount = user_amount  # to_amount in base
        else:
            # Case 3: foreign -> foreign
            # User amount is in from_currency, calculate to_amount in to_currency
            from_rate = Decimal(str(self._get_forex_rate(from_currency)))
            to_rate = Decimal(str(self._get_forex_rate(to_currency)))
            currency_amount = user_amount  # from_amount in from_currency
            to_amount = user_amount * (from_rate / to_rate)  # to_amount in to_currency

        return TransferDTO(
            date=transfer.date,
            from_account=transfer.from_account,
            to_account=transfer.to_account,
            amount=to_amount,
            notes=transfer.notes,
            currency=currency,
            currency_amount=currency_amount,
        )

    def add_expense(self, expense: ExpenseDTO) -> ExpenseRecord:
        """Add an expense and return the created record.
        
        For non-base currency accounts, automatically infers currency from account
        if only amount is provided. Automatically creates a sync record if enabled.
        """
        # Infer currency for non-base accounts
        expense = self._infer_currency_for_expense(expense)
        expense = self._apply_rounding_policy_expense(expense)
        
        return self._execute_create_transaction(
            insert_func=self.repository.insert_expense,
            record_dto=expense,
            validators=None,
            sync_operation="AddExpense",
        )

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

        amount_decimal_places = None
        currency_amount_decimal_places = None
        if amount is not None or currency_amount is not None:
            amount_decimal_places, currency_amount_decimal_places = self._resolve_rounding_policy(
                currency
            )
        
        return self._execute_update_transaction(
            update_func=self.repository.update_expense,
            key=key,
            normalized_params={
                "amount": amount,
                "notes": notes,
                "currency": currency,
                "currency_amount": currency_amount,
                "amount_decimal_places": amount_decimal_places,
                "currency_amount_decimal_places": currency_amount_decimal_places,
            },
            sync_operation="UpdateExpense",
        )

    def delete_expense(self, key: int) -> None:
        """Delete an expense and record the sync update."""
        return self._execute_delete_transaction(
            get_func=self.repository.get_expense,
            delete_func=self.repository.delete_expense,
            key=key,
            sync_operation="DeleteExpense",
        )

    def add_income(self, income: IncomeDTO) -> IncomeRecord:
        """Add an income record and return the created record.
        
        For non-base currency accounts, automatically infers currency from account
        if only amount is provided. Automatically creates a sync record if enabled.
        """
        # Infer currency for non-base accounts
        income = self._infer_currency_for_income(income)
        income = self._apply_rounding_policy_income(income)
        
        return self._execute_create_transaction(
            insert_func=self.repository.insert_income,
            record_dto=income,
            validators=None,
            sync_operation="AddIncome",
        )

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

        amount_decimal_places = None
        currency_amount_decimal_places = None
        if amount is not None or currency_amount is not None:
            amount_decimal_places, currency_amount_decimal_places = self._resolve_rounding_policy(
                currency
            )

        return self._execute_update_transaction(
            update_func=self.repository.update_income,
            key=key,
            normalized_params={
                "amount": amount,
                "notes": notes,
                "currency": currency,
                "currency_amount": currency_amount,
                "amount_decimal_places": amount_decimal_places,
                "currency_amount_decimal_places": currency_amount_decimal_places,
            },
            sync_operation="UpdateIncome",
        )

    def delete_income(self, key: int) -> None:
        """Delete an income record and record the sync update."""
        return self._execute_delete_transaction(
            get_func=self.repository.get_income,
            delete_func=self.repository.delete_income,
            key=key,
            sync_operation="DeleteIncome",
        )

    def add_transfer(self, transfer: TransferDTO) -> TransferRecord:
        """Add a transfer and return the created record.
        
        For mixed-currency transfers, defaults to from_account's currency if not specified.
        Automatically creates a sync record if sync is enabled.
        """
        # Infer currency from from_account for non-base accounts
        transfer = self._infer_currency_for_transfer(transfer)
        
        # Validate that currency matches from_account
        self._validate_transfer_currency_constraint(transfer)
        
        transfer = self._apply_rounding_policy_transfer(transfer)
        
        return self._execute_create_transaction(
            insert_func=self.repository.insert_transfer,
            record_dto=transfer,
            validators=None,
            sync_operation="AddTransfer",
        )

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

        amount_decimal_places = None
        currency_amount_decimal_places = None
        if amount is not None or currency_amount is not None:
            amount_decimal_places, currency_amount_decimal_places = self._resolve_rounding_policy(
                currency
            )

        return self._execute_update_transaction(
            update_func=self.repository.update_transfer,
            key=key,
            normalized_params={
                "amount": amount,
                "notes": notes,
                "currency": currency,
                "currency_amount": currency_amount,
                "amount_decimal_places": amount_decimal_places,
                "currency_amount_decimal_places": currency_amount_decimal_places,
            },
            sync_operation="UpdateTransfer",
        )

    def delete_transfer(self, key: int) -> None:
        """Delete a transfer and record the sync update."""
        return self._execute_delete_transaction(
            get_func=self.repository.get_transfer,
            delete_func=self.repository.delete_transfer,
            key=key,
            sync_operation="DeleteTransfer",
        )

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
            if currency is None or not currency.strip():
                raise ValueError(f"{label}: currency is required with currency_amount")
            if exchange_rate is None:
                exchange_rate = self._get_forex_rate(currency)
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
                dto = self._apply_rounding_policy_expense(dto)
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
                amount_decimal_places = None
                currency_amount_decimal_places = None
                if amount is not None or currency_amount is not None:
                    amount_decimal_places, currency_amount_decimal_places = (
                        self._resolve_rounding_policy(normalized_currency)
                    )
                record = self.repository.update_expense(
                    key=key,
                    amount=amount,
                    notes=normalized_notes,
                    currency=normalized_currency,
                    currency_amount=currency_amount,
                    amount_decimal_places=amount_decimal_places,
                    currency_amount_decimal_places=currency_amount_decimal_places,
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
                dto = self._apply_rounding_policy_income(dto)
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
                amount_decimal_places = None
                currency_amount_decimal_places = None
                if amount is not None or currency_amount is not None:
                    amount_decimal_places, currency_amount_decimal_places = (
                        self._resolve_rounding_policy(normalized_currency)
                    )
                record = self.repository.update_income(
                    key=key,
                    amount=amount,
                    notes=normalized_notes,
                    currency=normalized_currency,
                    currency_amount=currency_amount,
                    amount_decimal_places=amount_decimal_places,
                    currency_amount_decimal_places=currency_amount_decimal_places,
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
            dto = self._apply_rounding_policy_transfer(dto)
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
            amount_decimal_places = None
            currency_amount_decimal_places = None
            if amount is not None or currency_amount is not None:
                amount_decimal_places, currency_amount_decimal_places = (
                    self._resolve_rounding_policy(normalized_currency)
                )
            record = self.repository.update_transfer(
                key=key,
                amount=amount,
                notes=normalized_notes,
                currency=normalized_currency,
                currency_amount=currency_amount,
                amount_decimal_places=amount_decimal_places,
                currency_amount_decimal_places=currency_amount_decimal_places,
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
    def _execute_batch_create_transaction(
        self,
        items: list[object],
        insert_func: Callable,
        sync_operation_name: str,
        continue_on_error: bool = True,
    ) -> BatchResult:
        """Execute a batch create operation with consolidated sync.
        
        Base method for add_*_batch operations consolidating the pattern:
        - Disable sync during individual inserts
        - Process each item and collect successful/failed
        - Re-enable sync and create batch sync records
        
        Args:
            items: List of DTOs to insert (ExpenseDTO, IncomeDTO, TransferDTO)
            insert_func: Repository insert method (e.g., insert_expense)
            sync_operation_name: Operation name for sync (e.g., "AddExpense")
            continue_on_error: If True, continue after errors; if False, raise on first
            
        Returns:
            BatchResult with successful records and failures
        """
        successful: list[object] = []
        failed: list[tuple[object, Exception]] = []
        
        def action() -> BatchResult:
            original_sync_setting = self.enable_sync
            self.enable_sync = False
            
            try:
                for item in items:
                    try:
                        record = insert_func(item)
                        successful.append(record)
                    except Exception as exc:
                        if not continue_on_error:
                            raise
                        failed.append((item, exc))
                
                self.enable_sync = original_sync_setting
                if self.enable_sync:
                    manager = self._get_sync_manager()
                    if manager and successful:
                        for record in successful:
                            manager.create_sync_record(record, sync_operation_name)
                
                return BatchResult(successful=successful, failed=failed)
            finally:
                self.enable_sync = original_sync_setting
        
        return self._run_transaction(action)

    def add_expenses_batch(
        self,
        expenses: list[ExpenseDTO],
        continue_on_error: bool = True,
    ) -> BatchResult:
        """Add multiple expenses in a batch operation.
        
        Disables sync during individual inserts and performs consolidated sync
        after all successful inserts complete.
        
        Args:
            expenses: List of validated expense DTOs
            continue_on_error: If True, continue processing after errors; if False, raise on first
        
        Returns:
            BatchResult with successful records and any failures
        """
        expenses_with_policy = [
            self._apply_rounding_policy_expense(expense) for expense in expenses
        ]
        return self._execute_batch_create_transaction(
            items=expenses_with_policy,
            insert_func=self.repository.insert_expense,
            sync_operation_name="AddExpense",
            continue_on_error=continue_on_error,
        )

    def add_incomes_batch(
        self,
        incomes: list[IncomeDTO],
        continue_on_error: bool = True,
    ) -> BatchResult:
        """Add multiple income records in a batch operation.
        
        Disables sync during individual inserts and performs consolidated sync
        after all successful inserts complete.
        
        Args:
            incomes: List of validated income DTOs
            continue_on_error: If True, continue processing after errors; if False, raise on first
        
        Returns:
            BatchResult with successful records and any failures
        """
        incomes_with_policy = [
            self._apply_rounding_policy_income(income) for income in incomes
        ]
        return self._execute_batch_create_transaction(
            items=incomes_with_policy,
            insert_func=self.repository.insert_income,
            sync_operation_name="AddIncome",
            continue_on_error=continue_on_error,
        )

    def add_transfers_batch(
        self,
        transfers: list[TransferDTO],
        continue_on_error: bool = True,
    ) -> BatchResult:
        """Add multiple transfers in a batch operation.
        
        Disables sync during individual inserts and performs consolidated sync
        after all successful inserts complete.
        
        Args:
            transfers: List of validated transfer DTOs
            continue_on_error: If True, continue processing after errors; if False, raise on first
        
        Returns:
            BatchResult with successful records and any failures
        """
        transfers_with_policy = [
            self._apply_rounding_policy_transfer(transfer) for transfer in transfers
        ]
        return self._execute_batch_create_transaction(
            items=transfers_with_policy,
            insert_func=self.repository.insert_transfer,
            sync_operation_name="AddTransfer",
            continue_on_error=continue_on_error,
        )
