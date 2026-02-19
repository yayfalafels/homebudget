# HomeBudget wrapper CLI examples

## Table of contents

- [Overview](#overview)
- [UI Control Behavior](#ui-control-behavior)
- [Setup](#setup)
- [Configuration](#configuration)
- [Global options](#global-options)
- [Expense commands](#expense-commands)
- [Income commands](#income-commands)
- [Transfer commands](#transfer-commands)
- [Reference data commands](#reference-data-commands)
- [Batch import](#batch-import)
- [Output formats](#output-formats)

## Overview

The HomeBudget CLI provides access to database operations via command-line interface. All write operations (add, update, delete) automatically manage the HomeBudget UI to ensure data consistency.

## UI Control Behavior

**When sync is enabled (default):**
- HomeBudget UI automatically closes before database operations
- Database changes are applied atomically while UI is closed
- HomeBudget UI automatically reopens after operations complete
- This prevents data inconsistency and database locks during updates

Example sequence:
```
$ hb expense add --date 2026-02-17 --category "Food" --amount 25.50 --account "Wallet"
[UI closes] 
→ Database operation executes
→ SyncUpdate records created
[UI reopens]
Added expense 12345
```

**To disable sync (and UI control):**
```bash
homebudget --no-sync expense add [options]
```

When `--no-sync` is used:
- No SyncUpdate records are created
- UI control is disabled
- Database changes are applied without UI management
- Useful for maintenance and testing without affecting mobile devices

## Setup

Activate the main environment and run the CLI from the repository root.

```bash
.\.scripts\cmd\setup-env.cmd
.\env\Scripts\activate
```

## Configuration

The CLI reads a user config JSON file for HomeBudget settings such as the database path.

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

When the config file is present, the CLI uses db_path from config when --db is not provided.

Explicit db path override.

```bash
homebudget --db C:/path/to/homebudget.db expense list --limit 5
```

## Global options

```bash
homebudget --db "C:/path/to/homebudget.db" expense list
```

Override database path (instead of using config file).

### Sync Control

| Flag | Default | Effect |
|------|---------|--------|
| (no flag) | sync enabled | Enables SyncUpdate and automatic UI control |
| `--no-sync` | N/A | Disables SyncUpdate and automatic UI control |

When sync is enabled, the HomeBudget UI is automatically managed during database operations to ensure consistency.

```bash

Add an expense.

```bash
homebudget expense add \
  --date 2026-02-16 \
  --category Dining \
  --subcategory Restaurant \
  --amount 25.50 \
  --account Wallet \
  --notes "Lunch"
```

List expenses with filters.

```bash
homebudget expense list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28 \
  --account Wallet \
  --limit 50
```

Get a single expense by key.

```bash
homebudget expense get 13074
```

Update an expense.

```bash
homebudget expense update 13074 \
  --amount 27.50 \
  --notes "Lunch with tip"
```

Add an expense without sync.

```bash
homebudget --no-sync expense add \
  --date 2026-02-16 \
  --category Dining \
  --subcategory Restaurant \
  --amount 25.50 \
  --account Wallet \
  --notes "Lunch"
```

Delete an expense.

```bash
homebudget expense delete 13074 --yes
```

## Income commands

Add income.

```bash
homebudget income add \
  --date 2026-02-28 \
  --name "Salary" \
  --amount 5000.00 \
  --account Bank \
  --notes "February salary"
```

List income.

```bash
homebudget income list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```

Update income.

```bash
homebudget income update 14021 \
  --notes "Updated notes"
```

Delete income.

```bash
homebudget income delete 14021 --yes
```

## Transfer commands

Add a transfer.

```bash
homebudget transfer add \
  --date 2026-02-20 \
  --from-account Bank \
  --to-account Wallet \
  --amount 200.00 \
  --notes "Cash withdrawal"
```

List transfers.

```bash
homebudget transfer list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```

Update a transfer.

```bash
homebudget transfer update 15008 \
  --notes "Updated notes"
```

Delete a transfer.

```bash
homebudget transfer delete 15008 --yes
```

## Reference data commands

List accounts.

```bash
homebudget account list
```

List categories.

```bash
homebudget category list
```

List currencies.

```bash
homebudget currency list
```

## Batch import

Batch add expenses from a CSV file.

```bash
homebudget expense batch-add C:/path/to/expenses.csv
```

Batch add expenses from a JSON file.

```bash
homebudget expense batch-add C:/path/to/expenses.json --format json
```

Example JSON list for batch expenses.

```json
[
  {
    "date": "2026-02-16",
    "category": "Dining",
    "subcategory": "Restaurant",
    "amount": 25.50,
    "account": "Wallet",
    "notes": "Lunch"
  },
  {
    "date": "2026-02-16",
    "category": "Transport",
    "subcategory": "Taxi",
    "amount": 12.00,
    "account": "Wallet",
    "notes": "Cab home"
  }
]
```

Batch operations perform sync once after the batch completes.

## Output formats

JSON output for a list command.

```bash
homebudget --format json expense list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```

CSV output for a list command.

```bash
homebudget --format csv expense list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```
