# HomeBudget comprehensive guide

## Table of contents

- [Getting started](#getting-started)
- [Installation](#installation)
- [Configuration](#configuration)
- [Basic usage](#basic-usage)
- [Entry points](#entry-points)
- [Forex input rules](#forex-input-rules)
  - [Currency matching constraints](#currency-matching-constraints)
- [Feature mapping](#feature-mapping)
- [Working with expenses](#working-with-expenses)
- [Working with income](#working-with-income)
- [Working with transfers](#working-with-transfers)
- [Batch operations](#batch-operations)
- [Troubleshooting](#troubleshooting)

## Getting started

The HomeBudget wrapper is a Python library and CLI that lets you manage HomeBudget data through a SQLite database. The wrapper supports expense, income, and transfer operations with full CRUD (create, read, update, delete) functionality. It also supports sync updates so changes appear in the HomeBudget apps across all devices.

What you need
- Python 3.10 or later
- SQLite 3.35 or later
- A HomeBudget database file

## Installation

Using Git Bash on Windows for all examples. Clone the repository to access the project files.

```bash
git clone https://github.com/yayfalafels/homebudget.git
cd homebudget
```

Activate the main environment at `env/` (do not use `.dev/env` for normal workflows).

```bash
source env/Scripts/activate
```

Install the package from the wheel distribution.

```bash
pip install homebudget-*.whl
```

## Configuration

The wrapper requires a configuration file for database path and settings. See the [Configuration Guide](configuration.md) for complete setup instructions.

**Quick setup:**

```bash
# Create config directory and copy sample
config_dir="$USERPROFILE/OneDrive/Documents/HomeBudgetData"
mkdir -p "$config_dir"
cp config/hb-config.json.sample "$config_dir/hb-config.json"
# Edit the config file to set db_path
```

**Configuration file location:**
```
%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json
```

For full configuration options and troubleshooting, see [Configuration Guide](configuration.md).

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
- Provide `--db` for the database path when `hb-config.json` is not configured

## Sync behavior

Sync updates are enabled by default and mandatory for all write commands. This ensures consistency between local and remote devices:
- Creates SyncUpdate records in the database
- Enables mobile and other HomeBudget clients to synchronize changes
- Automatically manages the HomeBudget UI to maintain data consistency (Feature 001)

Sync cannot be disabled via the CLI to prevent irreparable breaks between local and remote data.

## Forex input rules

Forex inputs use one of two paths for expenses and income.

Base currency path
- Provide amount only
- Currency defaults to the account currency
- Currency amount is set to amount for base currency updates
- Exchange rate is treated as 1.0

Foreign currency path
- Provide currency and currency amount
- Exchange rate is optional (if omitted, the wrapper infers a rate from the forex cache)
- Amount is calculated as currency amount times exchange rate

You can pass an explicit rate with `--exchange-rate` (CLI) or `exchange_rate` (client updates).

Do not provide amount and currency amount together.

### Currency matching constraints

When adding or updating transactions (expense, income, transfer), the currency you specify must match the account's base currency rules:

**For expenses and income:**
- **Cannot add base currency transactions to non-base currency accounts**: If an account's currency is non-base (e.g., USD account "TWH IB USD"), you cannot add a transaction in the system's base currency (SGD). The account will reject base currency inputs.
- **Can add foreign currency transactions to base currency accounts**: If an account's currency is the system base (SGD), you can add transactions in foreign currencies (USD, EUR, GEL, etc.) by specifying `--currency`, `--currency-amount`, and optionally `--exchange-rate`.

**Examples:**
- ✓ VALID: Add USD expense to "TWH - Personal" (SGD base) with `--currency USD --currency-amount 27.50 --exchange-rate 0.9273`
- ✗ INVALID: Add SGD income to "TWH IB USD" (USD base) - account does not accept base currency
- ✓ VALID: Add USD income to "DBS Multi" (SGD base) with `--currency USD --currency-amount 2700 --exchange-rate 0.7407`

**For transfers between mixed-currency accounts:**
- You can specify the currency amount and exchange rate for **either the source or destination account's currency**, but not both
- Examples:
  - ✓ VALID: Transfer from "TWH - Personal" (SGD) to "TWH IB USD" (USD) specifying USD: `--currency USD --currency-amount 110 --exchange-rate 0.9091`
  - ✓ VALID: Same transfer specifying SGD: `--currency SGD --currency-amount 121 --exchange-rate 0.826`
  - ✗ INVALID: Mix both currencies in a single transfer - choose one accounts currency
  - ✗ INVALID: Specify a third currency (e.g., EUR) that does not match either account's currency

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

Use the transfer methods to add, list, update, and delete transfers between accounts. Transfers support a **currency normalization layer** that allows flexible input for mixed-currency transfers.

### Currency Normalization Layer

When transferring between accounts with different currencies, you can specify the amount in three ways:

- **Amount Only (Inference)**: Provide only `--amount`. The system infers the currency:

If base currency in either account → amount is in base currency

If base in neither account → amount is in from_account currency

- **From-Currency Explicit**: Provide `--currency` + `--currency-amount` matching the **from_account**

Already in backend format → passes through unchanged

- **To-Currency Explicit**: Provide `--currency` + `--currency-amount` matching the **to_account**

System normalizes to backend format using inverse forex calculation

For detailed normalization rules, see [docs/transfer-currency-normalization.md](transfer-currency-normalization.md).

### Basic Transfer Examples

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

Add a mixed-currency transfer (amount only).

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

### CLI Transfer Examples

Add a same-currency transfer.

```bash
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "Bank" \
  --to-account "Wallet" \
  --amount 200.00 \
  --notes "Cash withdrawal"
```

Add a mixed-currency transfer (amount only).

```bash
# Transfer from SGD to USD - amount inferred as base currency (SGD)
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "TWH - Personal" \
  --to-account "TWH IB USD" \
  --amount 200.00 \
  --notes "Transfer to USD account"
```

Add a mixed-currency transfer (explicit from-currency).

```bash
# Specify amount in from_account currency (USD)
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "TWH IB USD" \
  --to-account "TWH - Personal" \
  --currency USD \
  --currency-amount 150.00 \
  --exchange-rate 1.35 \
  --notes "Transfer to SGD account"
```

Add a mixed-currency transfer (explicit to-currency, normalized).

```bash
# Specify amount in to_account currency (EUR) - system normalizes
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "TWH IB USD" \
  --to-account "Cash TWH EUR" \
  --currency EUR \
  --currency-amount 90.00 \
  --exchange-rate 0.92 \
  --notes "Transfer to EUR account"
```

## Batch operations

Batch operations support two paths. Use batch import for single resource files, or use the mixed operation JSON format to combine resources and operations in one run.

### Batch behavior

- **Sync optimization**: Individual transactions are added without sync, then a single sync operation occurs after the batch completes
- **Error handling**: By default, batch continues on error and reports failures at the end. Use `--stop-on-error` to halt on first failure
- **Transaction atomicity**: Each individual transaction insert is atomic, but the batch as a whole may partially succeed
- **Validation**: Each record is validated before insertion same as single-record operations

### CSV format

CSV files must include a header row with these columns:

**Expense CSV columns:**

- `date` required: YYYY-MM-DD format
- `category` required: Category name
- `subcategory` optional: Subcategory name
- `amount` required: Decimal amount
- `account` required: Account name
- `notes` optional: Transaction notes
- `currency` optional: Currency code
- `currency_amount` optional: Foreign currency amount
- `exchange_rate` optional: Exchange rate to base currency

**Income CSV columns:**

- `date` required: YYYY-MM-DD format
- `name` required: Income name
- `amount` required: Decimal amount
- `account` required: Account name
- `notes` optional: Transaction notes
- `currency` optional: Currency code
- `currency_amount` optional: Foreign currency amount
- `exchange_rate` optional: Exchange rate to base currency

**Transfer CSV columns:**

- `date` required: YYYY-MM-DD format
- `from_account` required: Source account name
- `to_account` required: Destination account name
- `amount` optional: Destination amount Decimal
- `notes` optional: Transaction notes
- `currency` optional: Source Currency code
- `currency_amount` optional: Source currency amount
- `exchange_rate` optional: Exchange rate from currency -> to currency

**CSV example** for expenses.csv:
```csv
date,category,subcategory,amount,account,notes
2026-02-01,Food (Basic),Groceries,45.50,Wallet,Weekly groceries
2026-02-03,Transport,Fuel,60.00,Credit Card,Gas station
2026-02-05,Food (Basic),Cheap restaurant,15.75,Wallet,Lunch
```

### JSON format

JSON files must contain an array of transaction objects with the same fields as CSV columns.

**JSON example** for income.json:
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

**Transfer batch with currency normalization** - transfers_batch.json:
```json
[
  {
    "date": "2026-02-22",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "amount": "200.00",
    "notes": "SGD->USD Amount Only (inferred)"
  },
  {
    "date": "2026-02-22",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "currency": "SGD",
    "currency_amount": "250.00",
    "notes": "Explicit From Currency (SGD)"
  },
  {
    "date": "2026-02-22",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "currency": "USD",
    "currency_amount": "100.00",
    "notes": "Explicit To Currency (USD) - normalized to backend format"
  }
]
```

**Note**: Transfer batch imports support the currency normalization layer. You can specify `currency` + `currency_amount` for **either** the from_account **or** to_account. The system automatically normalizes to backend format (currency = from_account) during import.

### Mixed operation JSON format

Use this format to batch a mix of resources and CRUD operations in one file.

Each entry is a JSON object with these keys.

- `resource` with values expense, income, or transfer
- `operation` with values add, update, or delete
- `parameters` with the same fields used by the single record CLI commands

Example JSON for operations.json:

```json
[
  {
    "resource": "expense",
    "operation": "add",
    "parameters": {
      "date": "2026-02-16",
      "category": "Dining",
      "subcategory": "Restaurant",
      "amount": "25.50",
      "account": "Wallet",
      "notes": "Lunch"
    }
  },
  {
    "resource": "income",
    "operation": "update",
    "parameters": {
      "key": 14021,
      "notes": "Updated notes"
    }
  },
  {
    "resource": "transfer",
    "operation": "delete",
    "parameters": {
      "key": 21007
    }
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

**Run mixed batch operations:**
```bash
homebudget batch run --file operations.json
```

**Run mixed batch with stop-on-error:**
```bash
homebudget batch run --file operations.json --stop-on-error
```

**Run mixed batch with error report:**
```bash
homebudget batch run --file operations.json --error-report batch_errors.json
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

## Troubleshooting

- The setup script fails to install a dependency. Check requirements.txt and confirm the package source.
- The CLI reports a database error. Confirm the database file path is correct and that the file is not locked.
- Sync does not update the mobile app. Confirm sync is enabled and that DeviceInfo is present in the database.
- A duplicate error appears. Review existing transactions for matching date, account, amount, category, and notes.
- A command fails with a foreign currency error. Confirm the transaction currency matches the account currency.
- The Python version is too old. Install Python 3.10 or later and recreate the env directory.
- The SQLite version is too old. Use a Python build that includes SQLite 3.35 or later.

