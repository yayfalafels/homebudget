# HomeBudget wrapper CLI examples

## Table of contents

- [Overview](#overview)
- [UI Control Behavior](#ui-control-behavior)
- [Setup](#setup)
- [Configuration](#configuration)
- [Global options](#global-options)
- [Expense commands](#expense-commands)
- [Income commands](#income-commands)
- [UI control commands](#ui-control-commands)

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
  "db_path": "C:\\Users\\taylo\\OneDrive\\Documents\\HomeBudgetData\\Data\\homebudget.db"
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

## Expense commands

Forex rule
- Provide amount only for base currency
- Provide currency, currency amount, and exchange rate for foreign currency
- For base currency updates, currency amount matches amount

Add an expense using the account default currency.

```bash
homebudget expense add \
  --date 2026-02-16 \
  --category Dining \
  --subcategory Restaurant \
  --amount 25.50 \
  --account Wallet \
  --notes "Lunch"
```

Add an expense using a foreign currency and exchange rate.

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

Update an expense using the account default currency.

```bash
homebudget expense update 13074 \
  --amount 27.50 \
  --notes "Lunch with tip"
```

Update an expense using a foreign currency and exchange rate.

```bash
homebudget expense update 13074 \
  --currency EUR \
  --currency-amount 15.00 \
  --exchange-rate 1.08 \
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

Forex rule
- Provide amount only for base currency
- Provide currency, currency amount, and exchange rate for foreign currency
- For base currency updates, currency amount matches amount

Add income using the account default currency.

```bash
homebudget income add \
  --date 2026-02-28 \
  --name "Salary" \
  --amount 5000.00 \
  --account Bank \
  --notes "February salary"
```

Add income using a foreign currency and exchange rate.

```bash
homebudget income add \
  --date 2026-02-28 \
  --name "Salary" \
  --currency EUR \
  --currency-amount 4200.00 \
  --exchange-rate 1.19 \
  --account Bank \
  --notes "February salary"
```

List income.

```bash
homebudget income list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```

Update income using the account default currency.

```bash
homebudget income update 14021 \
  --notes "Updated notes"
```

Update income using a foreign currency and exchange rate.

```bash
homebudget income update 14021 \
  --currency EUR \
  --currency-amount 4500.00 \
  --exchange-rate 1.17 \
  --notes "Updated notes"
```

Delete income.

```bash
homebudget income delete 14021 --yes
```

## UI control commands

The CLI provides commands to control the HomeBudget UI application.

Start the HomeBudget UI.

```bash
homebudget ui start
```

Close the HomeBudget UI.

```bash
homebudget ui close
```

Refresh the HomeBudget UI (close and reopen).

```bash
homebudget ui refresh
```

Check the status of the HomeBudget UI.

```bash
homebudget ui status
```

Start UI with custom verification settings.

```bash
homebudget ui start --verify-attempts 10 --verify-delay 0.3 --settle-time 3.0
```

Close UI without verification.

```bash
homebudget ui close --no-verify
```

Refresh UI with force kill disabled.

```bash
homebudget ui refresh --no-force
```
