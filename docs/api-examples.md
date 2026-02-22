# HomeBudget wrapper API examples

## Table of contents

- [Setup](#setup)
- [Use config file](#use-config-file)
- [Add expense](#add-expense)
- [Add income](#add-income)
- [Add transfer](#add-transfer)
- [Update expense](#update-expense)
- [Delete expense](#delete-expense)
- [Handle duplicate expense](#handle-duplicate-expense)
- [Batch add expenses](#batch-add-expenses)
- [Mixed batch operations](#mixed-batch-operations)
- [Query transactions](#query-transactions)
- [Reference data lookups](#reference-data-lookups)

## Setup

Create a client and open the database using the configured default path.

```python
from homebudget import HomeBudgetClient

client = HomeBudgetClient()
```

Use the context manager to ensure clean shutdown.

```python
from homebudget import HomeBudgetClient

with HomeBudgetClient() as client:
    print("connected")
```

Explicit db path override.

```python
from homebudget import HomeBudgetClient

with HomeBudgetClient(db_path="C:/path/to/homebudget.db") as client:
    print("connected")
```

## Use config file

The client automatically loads configuration from the default location. Explicit loading is not required.

```python
from homebudget import HomeBudgetClient

# Configuration loaded automatically
with HomeBudgetClient() as client:
    expenses = client.list_expenses()
```

**Load from custom location:**

```python
import json
from pathlib import Path
from homebudget import HomeBudgetClient

# Explicitly specify database path
with HomeBudgetClient(db_path="C:/custom/path/homebudget.db") as client:
    expenses = client.list_expenses()
```

See [Configuration Guide](configuration.md) for details.

## Add expense

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

## Add income

```python
from decimal import Decimal
import datetime

from homebudget import HomeBudgetClient, IncomeDTO

with HomeBudgetClient() as client:
    income = IncomeDTO(
        date=datetime.date(2026, 2, 28),
        name="Salary",
        amount=Decimal("5000.00"),
        account="Bank",
        notes="February salary"
    )
    saved = client.add_income(income)
    print(saved.key)
```

## Add transfer

Add a same-currency transfer.

```python
from decimal import Decimal
import datetime

from homebudget import HomeBudgetClient, TransferDTO

with HomeBudgetClient() as client:
    transfer = TransferDTO(
        date=datetime.date(2026, 2, 20),
        from_account="Bank",
        to_account="Wallet",
        amount=Decimal("200.00"),
        notes="Cash withdrawal"
    )
    saved = client.add_transfer(transfer)
    print(saved.key)
```

Add a mixed-currency transfer (amount only, inferred).

```python
# Transfer from SGD account to USD account
# System infers: amount is in base currency (SGD)
with HomeBudgetClient() as client:
    transfer = TransferDTO(
        date=datetime.date(2026, 2, 20),
        from_account="TWH - Personal",  # SGD base
        to_account="TWH IB USD",  # USD
        amount=Decimal("200.00"),  # Interpreted as SGD
        notes="Transfer to USD account"
    )
    saved = client.add_transfer(transfer)
    print(saved.key)
```

Add a mixed-currency transfer (explicit from-currency).

```python
# Specify amount in from_account currency (USD)
with HomeBudgetClient() as client:
    transfer = TransferDTO(
        date=datetime.date(2026, 2, 20),
        from_account="TWH IB USD",  # USD
        to_account="TWH - Personal",  # SGD base
        amount=None,  # Will be calculated
        currency="USD",  # Matches from_account
        currency_amount=Decimal("150.00"),  # Amount in USD
        notes="Transfer to SGD account"
    )
    saved = client.add_transfer(transfer)
    print(saved.key)
```

Add a mixed-currency transfer (explicit to-currency, normalized).

```python
# Specify amount in to_account currency (EUR)
# System normalizes to backend format (from_account currency)
with HomeBudgetClient() as client:
    transfer = TransferDTO(
        date=datetime.date(2026, 2, 20),
        from_account="TWH IB USD",  # USD
        to_account="Cash TWH EUR",  # EUR
        amount=None,  # Will be calculated
        currency="EUR",  # Matches to_account (will be normalized)
        currency_amount=Decimal("90.00"),  # Amount in EUR
        notes="Transfer to EUR account"
    )
    saved = client.add_transfer(transfer)
    print(saved.key)
```

## Update expense

```python
from decimal import Decimal
from homebudget import HomeBudgetClient

with HomeBudgetClient() as client:
    updated = client.update_expense(
        key=13074,
        amount=Decimal("27.50"),
        notes="Lunch with tip"
    )
    print(updated.key, updated.amount)
```

## Delete expense

```python
from homebudget import HomeBudgetClient

with HomeBudgetClient() as client:
    client.delete_expense(13074)
```

## Handle duplicate expense

```python
from decimal import Decimal
import datetime

from homebudget import DuplicateError, ExpenseDTO, HomeBudgetClient

expense = ExpenseDTO(
    date=datetime.date(2026, 2, 16),
    category="Dining",
    subcategory="Restaurant",
    amount=Decimal("25.50"),
    account="Wallet",
    notes="Lunch"
)

with HomeBudgetClient() as client:
    try:
        client.add_expense(expense)
    except DuplicateError as exc:
        print(exc.details)
```

## Batch add expenses

Add multiple expenses in a single batch operation.

```python
from decimal import Decimal
import datetime
from homebudget import HomeBudgetClient, ExpenseDTO

expenses = [
    ExpenseDTO(
        date=datetime.date(2026, 2, 16),
        category="Dining",
        subcategory="Restaurant",
        amount=Decimal("25.50"),
        account="Wallet",
        notes="Lunch"
    ),
    ExpenseDTO(
        date=datetime.date(2026, 2, 16),
        category="Transport",
        subcategory="Taxi",
        amount=Decimal("12.00"),
        account="Wallet",
        notes="Cab home"
    ),
]

with HomeBudgetClient() as client:
    result = client.add_expenses_batch(expenses)
    print(f"Successful: {len(result.successful)}")
    print(f"Failed: {len(result.failed)}")
    for dto, error in result.failed:
        print(f"  Failed: {dto.date} {dto.amount} - {error}")
```

## Mixed batch operations

Execute multiple operations (add, update, delete) across different resources (expense, income, transfer) in a single batch.

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

## Query transactions

List expenses by date range.

```python
from homebudget import HomeBudgetClient
import datetime

with HomeBudgetClient() as client:
    results = client.list_expenses(
        start_date=datetime.date(2026, 2, 1),
        end_date=datetime.date(2026, 2, 28)
    )
    for expense in results:
        print(expense.key, expense.amount)
```

Get a single transaction by key.

```python
from homebudget import HomeBudgetClient

with HomeBudgetClient() as client:
    expense = client.get_expense(13074)
    print(expense.category, expense.amount)
```

List income with a date range filter.

```python
from homebudget import HomeBudgetClient
import datetime

with HomeBudgetClient() as client:
    results = client.list_income(
        start_date=datetime.date(2026, 2, 1),
        end_date=datetime.date(2026, 2, 28)
    )
    for income in results:
        print(income.key, income.amount)
```

## Reference data lookups

Accounts

```python
from homebudget import HomeBudgetClient

with HomeBudgetClient(db_path="C:/path/to/homebudget.db") as client:
    accounts = client.list_accounts()
    for account in accounts:
        print(account.name, account.currency)
```

Categories

```python
from homebudget import HomeBudgetClient

with HomeBudgetClient(db_path="C:/path/to/homebudget.db") as client:
    categories = client.list_categories()
    for category in categories:
        print(category.category, category.subcategory)
```

Currencies

```python
from homebudget import HomeBudgetClient

with HomeBudgetClient(db_path="C:/path/to/homebudget.db") as client:
    currencies = client.list_currencies()
    for currency in currencies:
        print(currency.code, currency.exchange_rate)
```
