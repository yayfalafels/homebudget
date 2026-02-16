# HomeBudget wrapper user guide

## Table of contents

- [Getting started](#getting-started)
- [Installation](#installation)
- [Basic usage](#basic-usage)
- [Entry points](#entry-points)
- [Working with expenses](#working-with-expenses)
- [Configuration](#configuration)
- [Common workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)
- [Feature mapping](#feature-mapping)

## Getting started

The HomeBudget wrapper is a Python library and CLI that lets you manage HomeBudget data through a SQLite database. The wrapper supports expense, income, and transfer operations plus reference data queries. It also supports sync updates so changes appear in the HomeBudget apps.

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
  "db_path": "C:\\Users\\taylo\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db",
  "sync_enabled": true
}
```

## Basic usage

For a complete set of examples, see the API and CLI example documents.

- API examples: [docs/api-examples.md](api-examples.md)
- CLI examples: [docs/cli-examples.md](cli-examples.md)

## Entry points

Library entry point
- Use the `HomeBudgetClient` class to perform CRUD operations and reference lookups
- Use DTO classes to validate data before writing to the database

CLI entry point
- Use `homebudget` or `hb` for the command line interface
- Provide `--db` for the database path and `--format` for output control

Sync behavior
- Sync updates are enabled by default for write commands
- Use `--no-sync` to disable sync updates for batch work

Batch behavior
- Use HomeBudgetClient batch for bulk add operations with a list of records
- Batch runs validation per record and performs sync once after the batch completes

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

## Configuration

The wrapper reads a user config JSON file for HomeBudget settings such as the database path.

Config file path
- %USER_PROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json

Default database path
- %USER_PROFILE%\OneDrive\Documents\HomeBudgetData\Data\homebudget.db

Config file example

```json
{
  "db_path": "C:\\Users\\taylo\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db",
  "sync_enabled": true
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
| List income | HomeBudgetClient.list_income | homebudget income list |
| Get income | HomeBudgetClient.get_income | homebudget income get |
| Update income | HomeBudgetClient.update_income | homebudget income update |
| Delete income | HomeBudgetClient.delete_income | homebudget income delete |
| Add transfer | HomeBudgetClient.add_transfer | homebudget transfer add |
| List transfers | HomeBudgetClient.list_transfers | homebudget transfer list |
| Get transfer | HomeBudgetClient.get_transfer | homebudget transfer get |
| Update transfer | HomeBudgetClient.update_transfer | homebudget transfer update |
| Delete transfer | HomeBudgetClient.delete_transfer | homebudget transfer delete |
| Batch add expenses | HomeBudgetClient.batch | homebudget expense batch-add |
| List accounts | HomeBudgetClient.list_accounts | homebudget account list |
| List categories | HomeBudgetClient.list_categories | homebudget category list |
| List currencies | HomeBudgetClient.list_currencies | homebudget currency list |
