# HomeBudget wrapper user guide

## Table of contents

- [Getting started](#getting-started)
- [Installation](#installation)
- [Basic usage](#basic-usage)
- [Entry points](#entry-points)
- [Forex input rules](#forex-input-rules)
- [Working with expenses](#working-with-expenses)
- [Working with income](#working-with-income)
- [Working with transfers](#working-with-transfers)
- [Batch operations](#batch-operations)
- [Configuration](#configuration)
- [Common workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)
- [Feature mapping](#feature-mapping)

## Getting started

The HomeBudget wrapper is a Python library and CLI that lets you manage HomeBudget data through a SQLite database. The wrapper supports expense and income operations. It also supports sync updates so changes appear in the HomeBudget apps.

What you need
- Python 3.10 or later
- SQLite 3.35 or later
- A HomeBudget database file

## Installation

Use the repository setup scripts to create the main environment and install dependencies.

Windows

```bash
.\.scripts\cmd\setup-env.cmd
.\env\Scripts\activate
```

Bash

```bash
./.scripts/bash/setup-env.sh
source env/bin/activate
```

Install the package in editable mode for local development.

```bash
pip install -e src/python
```

Create the user config JSON once during setup. A sample config is provided in `config/hb-config.json.sample`.

Config file path
- %USER_PROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json

Default database path
- %USER_PROFILE%\OneDrive\Documents\HomeBudgetData\Data\homebudget.db

Setup instructions

```powershell
# Copy the sample config to your HomeBudgetData directory
$configDir = "$env:USERPROFILE\OneDrive\Documents\HomeBudgetData"
New-Item -ItemType Directory -Force -Path $configDir
Copy-Item config\hb-config.json.sample "$configDir\hb-config.json"
# Edit the config file to set db_path to your operational homebudget.db
```

Config file format

```json
{
  "db_path": "C:\\Users\\taylo\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db"
}
```

## Basic usage

For a complete set of examples, see the API and CLI example documents.

- API examples: [docs/api-examples.md](api-examples.md)
- CLI examples: [docs/cli-examples.md](cli-examples.md)

## Entry points

Library entry point
- Use the `HomeBudgetClient` class to perform CRUD operations
- Use DTO classes to validate data before writing to the database

CLI entry point
- Use `homebudget` or `hb` for the command line interface
- Provide `--db` for the database path

### Sync behavior

Sync updates are enabled by default for write commands, which:
- Creates SyncUpdate records in the database
- Enables mobile and other HomeBudget clients to synchronize changes
- Automatically manages the HomeBudget UI to maintain data consistency (Feature 001)

Use `--no-sync` to disable sync updates:
```bash
homebudget --no-sync expense add [options]
```

## Forex input rules

Forex inputs use one of two paths for expenses and income.

Base currency path
- Provide amount only
- Currency defaults to the account currency
- Currency amount is set to amount for base currency updates
- Exchange rate is treated as 1.0

Foreign currency path
- Provide currency, currency amount, and exchange rate
- Amount is calculated as currency amount times exchange rate

Do not provide amount and currency amount together, except when they are equal for base currency updates.

### UI Control (Automatic)

When you run a write command with sync enabled (the default), the HomeBudget UI is **automatically closed** during the database operation and **automatically reopened** when complete.

**Why this happens:**
- Ensures the UI doesn't read incomplete data during database changes
- Prevents database locks that occur while the UI reads during sync operations
- Atomic database transactions are guaranteed without UI interference

**What you'll observe:**
- The HomeBudget application window will briefly close and reopen
- The entire operation (close → change → reopen) typically takes 6-11 seconds
- No manual intervention is needed; it's completely automated

**Disabling UI control:**
Use `--no-sync` to disable both sync and UI control:
```bash
homebudget --no-sync expense add --date 2026-02-17 --category "Food" --amount 25.50 --account "Wallet"
```

This is useful for:
- Maintenance tasks where sync should not happen
- Testing without affecting mobile devices
- Operations where you want to manage UI control manually

## Working with expenses

Use the expense methods to add, list, update, and delete transactions. Sync updates are created for write operations when sync is enabled.

Add an expense.

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

List expenses for a date range.

```python
import datetime
from homebudget import HomeBudgetClient

with HomeBudgetClient() as client:
  results = client.list_expenses(
    start_date=datetime.date(2026, 2, 1),
    end_date=datetime.date(2026, 2, 28)
  )
  for expense in results:
    print(expense.key, expense.amount)
```

Add an expense with the CLI.

```bash
homebudget expense add \
  --date 2026-02-16 \
  --category Dining \
  --subcategory Restaurant \
  --amount 25.50 \
  --account Wallet \
  --notes "Lunch"
```

Add an expense with a foreign currency and exchange rate.

```bash
homebudget expense add \
  --date 2026-02-16 \
  --category Dining \
  --subcategory Restaurant \
  --currency EUR \
  --currency-amount 12.00 \
  --exchange-rate 1.10 \
  --account Wallet \
  --notes "Lunch"
```

## Working with income

Use the income methods to add, list, update, and delete income transactions. Sync updates are created for write operations when sync is enabled.

Add income.

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

List income for a date range.

```python
import datetime
from homebudget import HomeBudgetClient

with HomeBudgetClient() as client:
  results = client.list_incomes(
    start_date=datetime.date(2026, 2, 1),
    end_date=datetime.date(2026, 2, 28)
  )
  for income in results:
    print(income.key, income.amount)
```

Add income with the CLI.

```bash
homebudget income add \
  --date 2026-02-28 \
  --name "Salary" \
  --amount 5000.00 \
  --account Bank \
  --notes "February salary"
```

## Working with transfers

Use the transfer methods to add, list, update, and delete transfers between accounts. Sync updates are created for write operations when sync is enabled.

Add a transfer.

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

List transfers for a date range.

```python
import datetime
from homebudget import HomeBudgetClient

with HomeBudgetClient() as client:
  results = client.list_transfers(
    start_date=datetime.date(2026, 2, 1),
    end_date=datetime.date(2026, 2, 28)
  )
  for transfer in results:
    print(transfer.key, transfer.amount)
```

Add a transfer with the CLI.

```bash
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "Bank" \
  --to-account "Wallet" \
  --amount 200.00 \
  --notes "Cash withdrawal"
```

## Configuration

The wrapper reads a user config JSON file for HomeBudget settings such as the database path.

Config file path
- %USER_PROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json

Default database path
- %USER_PROFILE%\OneDrive\Documents\HomeBudgetData\Data\homebudget.db

Config file example

```json
{
  "db_path": "C:\\Users\\taylo\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db"
}
```

Client behavior
- HomeBudgetClient uses db_path from config when not provided

CLI behavior
- CLI uses db_path from config when --db is not provided

### API quick start

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

### CLI quick start

```bash
homebudget expense add \
  --date 2026-02-16 \
  --category Dining \
  --subcategory Restaurant \
  --amount 25.50 \
  --account Wallet \
  --notes "Lunch"
```

## Batch operations

Batch operations enable importing multiple transactions at once from CSV or JSON files. This is useful for statement-driven updates where you need to add many transactions efficiently.

### Batch behavior

- **Sync optimization**: Individual transactions are added without sync, then a single sync operation occurs after the batch completes
- **Error handling**: By default, batch continues on error and reports failures at the end. Use `--stop-on-error` to halt on first failure
- **Transaction atomicity**: Each individual transaction insert is atomic, but the batch as a whole may partially succeed
- **Validation**: Each record is validated before insertion same as single-record operations

### CSV format

CSV files must include a header row with these columns:

**Expense CSV columns:**
- `date` (required): YYYY-MM-DD format
- `category` (required): Category name
- `subcategory` (optional): Subcategory name
- `amount` (required): Decimal amount
- `account` (required): Account name
- `notes` (optional): Transaction notes
- `currency` (optional): Currency code
- `currency_amount` (optional): Foreign currency amount
- `exchange_rate` (optional): Exchange rate to base currency

**Income CSV columns:**
- `date` (required): YYYY-MM-DD format
- `name` (required): Income name
- `amount` (required): Decimal amount
- `account` (required): Account name
- `notes` (optional): Transaction notes
- `currency` (optional): Currency code
- `currency_amount` (optional): Foreign currency amount
- `exchange_rate` (optional): Exchange rate to base currency

**Transfer CSV columns:**
- `date` (required): YYYY-MM-DD format
- `from_account` (required): Source account name
- `to_account` (required): Destination account name
- `amount` (required): Decimal amount
- `notes` (optional): Transaction notes
- `currency` (optional): Currency code
- `currency_amount` (optional): Foreign currency amount
- `exchange_rate` (optional): Exchange rate to base currency

**CSV example** (expenses.csv):
```csv
date,category,subcategory,amount,account,notes
2026-02-01,Food (Basic),Groceries,45.50,Wallet,Weekly groceries
2026-02-03,Transport,Fuel,60.00,Credit Card,Gas station
2026-02-05,Food (Basic),Cheap restaurant,15.75,Wallet,Lunch
```

### JSON format

JSON files must contain an array of transaction objects with the same fields as CSV columns.

**JSON example** (income.json):
```json
[
  {
    "date": "2026-02-01",
    "name": "Salary",
    "amount": "5000.00",
    "account": "Checking",
    "notes": "Monthly salary"
  },
  {
    "date": "2026-02-15",
    "name": "Freelance",
    "amount": "1200.00",
    "account": "Checking",
    "notes": "Project payment"
  }
]
```

### API usage

```python
from homebudget import HomeBudgetClient
from homebudget.models import ExpenseDTO
from decimal import Decimal
import datetime as dt

with HomeBudgetClient() as client:
    expenses = [
        ExpenseDTO(
            date=dt.date(2026, 2, 1),
            category="Food (Basic)",
            subcategory="Groceries",
            amount=Decimal("45.50"),
            account="Wallet",
            notes="Weekly groceries"
        ),
        ExpenseDTO(
            date=dt.date(2026, 2, 3),
            category="Transport",
            subcategory="Fuel",
            amount=Decimal("60.00"),
            account="Credit Card",
            notes="Gas station"
        )
    ]
    
    result = client.add_expenses_batch(expenses)
    print(f"Successful: {len(result.successful)}")
    print(f"Failed: {len(result.failed)}")
    for dto, error in result.failed:
        print(f"  Failed: {dto.date} {dto.amount} - {error}")
```

### CLI usage

**Import expenses from CSV:**
```bash
homebudget expense batch-import --file expenses.csv --format csv
```

**Import income from JSON:**
```bash
homebudget income batch-import --file income.json --format json
```

**Import with error report:**
```bash
homebudget expense batch-import --file expenses.csv --format csv --error-report errors.txt
```

**Stop on first error:**
```bash
homebudget transfer batch-import --file transfers.csv --format csv --stop-on-error
```

### Batch result output

The CLI displays a summary of batch results:

```
Batch import completed
=====================
Total records: 25
Successful: 23
Failed: 2

Failed records:
  Row 15: 2026-02-10 45.50 - DuplicateError: Matching expense already exists
  Row 22: 2026-02-18 invalid - ValueError: Invalid amount format

Sync completed for 23 transactions
```

If `--error-report` is specified, failed records are written to the file with details.

## Common workflows

The wrapper supports the same workflow used for financial statement updates.

Pre-flight checks
- Confirm access to account statements
- Confirm the HomeBudget database is current

Forex
- Fetch USD SGD rates and update the rates sheet

Account update
- Add expenses, income, and transfers as statements are reviewed
- Use batch import for statement driven updates

Report update
- Use list commands to review totals and spot errors
- Confirm no duplicate entries before report export
- Save statements as PDF after review

## Troubleshooting

- The setup script fails to install a dependency. Check requirements.txt and confirm the package source.
- The CLI reports a database error. Confirm the database file path is correct and that the file is not locked.
- Sync does not update the mobile app. Confirm sync is enabled and that DeviceInfo is present in the database.
- A duplicate error appears. Review existing transactions for matching date, account, amount, category, and notes.
- A command fails with a foreign currency error. Confirm the transaction currency matches the account currency.
- The Python version is too old. Install Python 3.10 or later and recreate the env directory.
- The SQLite version is too old. Use a Python build that includes SQLite 3.35 or later.

## Feature mapping

| HomeBudget UI operation | Wrapper method | CLI command |
| --- | --- | --- |
| Add expense | HomeBudgetClient.add_expense | homebudget expense add |
| List expenses | HomeBudgetClient.list_expenses | homebudget expense list |
| Get expense | HomeBudgetClient.get_expense | homebudget expense get |
| Update expense | HomeBudgetClient.update_expense | homebudget expense update |
| Delete expense | HomeBudgetClient.delete_expense | homebudget expense delete |
| Add income | HomeBudgetClient.add_income | homebudget income add |
| List income | HomeBudgetClient.list_incomes | homebudget income list |
| Get income | HomeBudgetClient.get_income | homebudget income get |
| Update income | HomeBudgetClient.update_income | homebudget income update |
| Delete income | HomeBudgetClient.delete_income | homebudget income delete |
| Add transfer | HomeBudgetClient.add_transfer | homebudget transfer add |
| List transfers | HomeBudgetClient.list_transfers | homebudget transfer list |
| Get transfer | HomeBudgetClient.get_transfer | homebudget transfer get |
| Update transfer | HomeBudgetClient.update_transfer | homebudget transfer update |
| Delete transfer | HomeBudgetClient.delete_transfer | homebudget transfer delete |
| Batch add expenses | HomeBudgetClient.add_expenses_batch | homebudget expense batch-import |
| Batch add income | HomeBudgetClient.add_incomes_batch | homebudget income batch-import |
| Batch add transfers | HomeBudgetClient.add_transfers_batch | homebudget transfer batch-import |
| Start UI | N/A | homebudget ui start |
| Close UI | N/A | homebudget ui close |
| Refresh UI | N/A | homebudget ui refresh |
| Check UI status | N/A | homebudget ui status |
