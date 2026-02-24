# HomeBudget Wrapper Methods Guide

## Table of contents

- [Overview](#overview)
- [Quick start](#quick-start)
- [Client methods](#client-methods)
- [Account methods](#account-methods)
- [Expense methods](#expense-methods)
- [Income methods](#income-methods)
- [Transfer methods](#transfer-methods)
- [Batch methods](#batch-methods)
- [Reference data methods](#reference-data-methods)
- [Data transfer objects](#data-transfer-objects)

## Overview

The HomeBudget wrapper exposes methods for programmatic database access. All write operations automatically manage sync updates and can be used within a context manager or with explicit lifecycle management.

## Quick start

Create a client using the configured default database path:

```python
from homebudget import HomeBudgetClient

with HomeBudgetClient() as client:
    expense = client.add_expense(...)
```

Override the database path:

```python
with HomeBudgetClient(db_path="C:/path/to/homebudget.db") as client:
    expenses = client.list_expenses()
```

## Client methods

### Lifecycle

**`__init__(db_path=None, enable_sync=True)`**

Initialize the client. If `db_path` is omitted, the configured default is used. Sync is enabled by default and cannot be disabled.

**`close()`**

Close the database connection. Called automatically when using the context manager.

**`__enter__()`, `__exit__()`**

Context manager support. Ensures clean shutdown via `close()`.

```python
with HomeBudgetClient() as client:
    # use client
    pass  # closes automatically
```

## Account methods

**`get_account_balance(account: str, query_date: datetime.date = None) -> BalanceRecord`**

Query the account balance on a specific date. The balance is calculated from the most recent reconcile (balance) record for the account, then adjusted forward or backward through transactions to the query date.

If `query_date` is omitted, today's date is used.

Raises `NotFoundError` if the account cannot be found or has no reconcile balance record.

```python
import datetime
from homebudget import HomeBudgetClient

with HomeBudgetClient() as client:
    # Query today's balance
    balance = client.get_account_balance("Wallet")
    print(f"{balance.accountName}: {balance.balanceAmount} on {balance.queryDate}")
    
    # Query balance on a specific date
    past_balance = client.get_account_balance(
        "TWH - Personal",
        query_date=datetime.date(2026, 2, 1)
    )
    print(f"Balance: {past_balance.balanceAmount}")
    print(f"Reconcile: {past_balance.reconcileAmount} on {past_balance.reconcileDate}")
```

**How it works:**

- **Exact reconcile date:** If the query date matches a reconcile date in the account's transaction history, the balance equals the reconcile amount
- **After reconcile date:** The balance is calculated forward by starting with the reconcile amount and adding income/transfer_in transactions and subtracting expense/transfer_out transactions from the reconcile date through the query date
- **Before reconcile date:** The balance is calculated backward by reversing the transaction adjustments between the query date and the reconcile date
- **Transaction amounts:** All transaction amounts are stored as positive values in the database; the calculation logic applies the appropriate signs based on transaction type

## Expense methods

**`add_expense(expense: ExpenseDTO) -> ExpenseRecord`**

Add a single expense. For base currency accounts, provide `amount` only. For foreign currency accounts, provide `currency`, `currency_amount`, and `exchange_rate`. Returns the saved record with generated key.

```python
from decimal import Decimal
import datetime
from homebudget import HomeBudgetClient, ExpenseDTO

with HomeBudgetClient() as client:
    expense = ExpenseDTO(
        date=datetime.date(2026, 2, 16),
        category="Dining",
        subcategory="Restaurant",
        amount=Decimal("25.50"),
        account="Wallet",
        notes="Lunch"
    )
    saved = client.add_expense(expense)
    print(saved.key)
```

**`get_expense(key: int) -> ExpenseRecord`**

Retrieve a single expense by key.

**`list_expenses(start_date=None, end_date=None, account=None, category=None, limit=None) -> list[ExpenseRecord]`**

List expenses with optional filters. Date range is inclusive. Returns all matching expenses up to the limit.

```python
import datetime
results = client.list_expenses(
    start_date=datetime.date(2026, 2, 1),
    end_date=datetime.date(2026, 2, 28),
    account="Wallet",
    limit=50
)
```

**`update_expense(key: int, **fields) -> ExpenseRecord`**

Update specific fields of an existing expense. Accepts `amount`, `currency`, `currency_amount`, `exchange_rate`, `category`, `subcategory`, `account`, `date`, `notes`. Returns the updated record.

```python
from decimal import Decimal

updated = client.update_expense(
    13074,
    amount=Decimal("27.50"),
    notes="Updated"
)
```

**`delete_expense(key: int) -> None`**

Delete an expense by key.

### Income methods

**`add_income(income: IncomeDTO) -> IncomeRecord`**

Add a single income. Currency handling matches expense methods. Returns the saved record with generated key.

**`get_income(key: int) -> IncomeRecord`**

Retrieve a single income by key.

**`list_income(start_date=None, end_date=None, account=None, limit=None) -> list[IncomeRecord]`**

List income with optional filters. Date range is inclusive. Returns all matching income up to the limit.

**`update_income(key: int, **fields) -> IncomeRecord`**

Update specific fields of an existing income. Accepts `amount`, `currency`, `currency_amount`, `exchange_rate`, `name`, `account`, `date`, `notes`. Returns the updated record.

**`delete_income(key: int) -> None`**

Delete an income by key.

### Transfer methods

**`add_transfer(transfer: TransferDTO) -> TransferRecord`**

Add a transfer between accounts. The normalization layer accepts `currency` for either the from_account or to_account. Returns the saved record with generated key.

To specify the sending amount (from_account currency):

```python
from decimal import Decimal
import datetime

transfer = TransferDTO(
    date=datetime.date(2026, 2, 22),
    from_account="Wallet",
    to_account="Bank Account",
    currency="SGD",
    currency_amount=Decimal("100.00"),
    exchange_rate=Decimal("1.0"),
    notes="Wallet to bank"
)
saved = client.add_transfer(transfer)
```

To specify the receiving amount (to_account currency), the system automatically calculates the corresponding from_account amount using the forex rate:

```python
transfer = TransferDTO(
    date=datetime.date(2026, 2, 22),
    from_account="TWH - Personal",  # SGD base
    to_account="TWH IB USD",  # USD
    currency="USD",
    currency_amount=Decimal("100.00"),
    exchange_rate=Decimal("0.74"),
    notes="SGD to USD"
)
# Internally normalized to: currency=SGD, currency_amount=135.14, amount=100.00
saved = client.add_transfer(transfer)
```

**`get_transfer(key: int) -> TransferRecord`**

Retrieve a single transfer by key.

**`list_transfers(start_date=None, end_date=None, from_account=None, to_account=None, limit=None) -> list[TransferRecord]`**

List transfers with optional filters. Date range is inclusive. Returns all matching transfers up to the limit.

**`update_transfer(key: int, **fields) -> TransferRecord`**

Update specific fields of an existing transfer. Accepts `from_account`, `to_account`, `amount`, `currency`, `currency_amount`, `exchange_rate`, `date`, `notes`. Returns the updated record.

**`delete_transfer(key: int) -> None`**

Delete a transfer by key.

### Batch methods

**`batch(operations: list[BatchOperation], continue_on_error=False) -> BatchResult`**

Execute mixed operations (add, update, delete) across expense, income, and transfer resources atomically. If `continue_on_error=True`, failed operations do not prevent subsequent operations. Returns a result object with `successful` and `failed` lists.

```python
from homebudget import HomeBudgetClient, BatchOperation

operations = [
    BatchOperation(
        resource="expense",
        operation="add",
        parameters={
            "date": "2026-02-20",
            "category": "Food (Basic)",
            "subcategory": "Restaurant",
            "amount": "25.50",
            "account": "TWH - Personal",
            "notes": "Lunch"
        }
    ),
    BatchOperation(
        resource="income",
        operation="update",
        parameters={
            "key": 14021,
            "notes": "Updated notes"
        }
    ),
    BatchOperation(
        resource="transfer",
        operation="delete",
        parameters={
            "key": 21007
        }
    )
]

with HomeBudgetClient() as client:
    result = client.batch(operations, continue_on_error=True)
    print(f"Successful: {len(result.successful)}")
    print(f"Failed: {len(result.failed)}")
    for op, error in result.failed:
        print(f"  Failed: {op.resource} {op.operation} - {error}")
```

**`add_expenses_batch(expenses: list[ExpenseDTO]) -> BatchResult`**

Batch import multiple expenses. Returns result with successful and failed lists.

**`add_incomes_batch(incomes: list[IncomeDTO]) -> BatchResult`**

Batch import multiple income records. Returns result with successful and failed lists.

**`add_transfers_batch(transfers: list[TransferDTO]) -> BatchResult`**

Batch import multiple transfers. Returns result with successful and failed lists.

### Reference data methods

**`list_accounts() -> list[AccountDTO]`**

Retrieve all configured accounts with their names and currencies.

```python
with HomeBudgetClient() as client:
    accounts = client.list_accounts()
    for account in accounts:
        print(account.name, account.currency)
```

**`list_categories() -> list[CategoryDTO]`**

Retrieve all available expense and income categories with their subcategories.

```python
with HomeBudgetClient() as client:
    categories = client.list_categories()
    for category in categories:
        print(category.category, category.subcategory)
```

**`list_currencies() -> list[CurrencyDTO]`**

Retrieve all available currencies with their exchange rates against the base currency.

```python
with HomeBudgetClient() as client:
    currencies = client.list_currencies()
    for currency in currencies:
        print(currency.code, currency.exchange_rate)
```

## Data transfer objects

### BalanceRecord

**`BalanceRecord`** (read-only result object returned by `get_account_balance()`)

Fields: `accountKey` (int), `accountName` (str), `queryDate` (datetime.date), `balanceAmount` (Decimal), `reconcileDate` (datetime.date), `reconcileAmount` (Decimal).

This frozen dataclass represents an account's balance at a specific date, calculated from the most recent reconcile balance and adjusted through transactions. All balance calculations are based on the most recent reconcile record found on or before the query date.

### Transaction DTOs

**`ExpenseDTO`**

Fields: `date`, `category`, `subcategory`, `amount` (or `currency_amount`), `currency` (optional), `exchange_rate` (optional), `account`, `notes` (optional).

**`IncomeDTO`**

Fields: `date`, `name`, `amount` (or `currency_amount`), `currency` (optional), `exchange_rate` (optional), `account`, `notes` (optional).

**`TransferDTO`**

Fields: `date`, `from_account`, `to_account`, `amount` (optional), `currency` (optional), `currency_amount` (optional), `exchange_rate` (optional), `notes` (optional).

For transfers, the normalization layer accepts currency specification for either account and calculates the corresponding other amount. See [Transfer Currency Normalization](transfer-currency-normalization.md) for details.

### Record DTOs

**`ExpenseRecord`**

Fields: `key`, `date`, `category`, `subcategory`, `amount`, `currency`, `currency_amount`, `exchange_rate`, `account`, `notes`, `created_at`, `updated_at`.

**`IncomeRecord`**

Fields: `key`, `date`, `name`, `amount`, `currency`, `currency_amount`, `exchange_rate`, `account`, `notes`, `created_at`, `updated_at`.

**`TransferRecord`**

Fields: `key`, `date`, `from_account`, `to_account`, `amount`, `currency`, `currency_amount`, `exchange_rate`, `notes`, `created_at`, `updated_at`.

### Reference data DTOs

**`AccountDTO`**

Fields: `name`, `currency`, `account_type`.

**`CategoryDTO`**

Fields: `category`, `subcategory`, `transaction_type`.

**`CurrencyDTO`**

Fields: `code`, `exchange_rate`.

### Batch operation DTOs

**`BatchOperation`**

Fields: `resource` (expense, income, or transfer), `operation` (add, update, or delete), `parameters` (dict of operation-specific fields).

**`BatchResult`**

Fields: `successful` (list of tuples: operation, result), `failed` (list of tuples: operation, error).
