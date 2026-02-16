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

Load the user config JSON and let the client use the configured db_path.

```python
import json
import os
from pathlib import Path
from homebudget import HomeBudgetClient

config_path = Path(os.environ["USER_PROFILE"]) / "OneDrive" / "Documents" / "HomeBudgetData" / "hb-config.json"

with config_path.open("r", encoding="utf-8") as handle:
    config = json.load(handle)

with HomeBudgetClient() as client:
    print("connected")
```

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

Use a batch call with resource and operation values and a list of expense records.

```python
from decimal import Decimal
import datetime
from homebudget import HomeBudgetClient, ExpenseDTO

records = [
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
    results = client.batch(
        resource="expense",
        operation="add",
        records=records
    )
    print(len(results))
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
