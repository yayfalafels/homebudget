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
- [Batch commands](#batch-commands)
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

## Setup

After setting up the virutal env and installing dependencies, activate the main environment and run the CLI from the repository root.

```bash
source env/Scripts/activate
```

## Configuration

The CLI uses a configuration file for database path and settings. For complete setup and configuration options, see the [Configuration Guide](configuration.md).

**Quick reference:**
- Config location: `%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json`
- Sample: `config/hb-config.json.sample`

**Override config:**
```bash
homebudget --db "C:/path/to/homebudget.db" expense list
```

## Global options

```bash
homebudget --db "C:/path/to/homebudget.db" expense list
```

Override database path (instead of using config file).

### Sync Control

Sync updates are enabled by default and cannot be disabled via CLI. This ensures consistency between local and remote devices.

When a write command is executed:
- SyncUpdate records are automatically created
- The HomeBudget UI is automatically managed to prevent conflicts
- Mobile and other clients can synchronize changes

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

## Transfer commands

Transfers support a **currency normalization layer** that allows flexible input for mixed-currency transfers. You can specify the amount in either the from_account or to_account currency.

Add a same-currency transfer.

```bash
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "Bank" \
  --to-account "Wallet" \
  --amount 200.00 \
  --notes "Cash withdrawal"
```

Add a mixed-currency transfer (amount only, inferred).

```bash
# Transfer from SGD account to USD account
# System infers: amount is in base currency (SGD)
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

List transfers.

```bash
homebudget transfer list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```

Get a single transfer by key.

```bash
homebudget transfer get 21007
```

Update a transfer.

```bash
homebudget transfer update 21007 \
  --amount 250.00 \
  --notes "Updated transfer amount"
```

Update a transfer with foreign currency.

```bash
homebudget transfer update 21007 \
  --currency USD \
  --currency-amount 180.00 \
  --exchange-rate 1.35 \
  --notes "Updated with explicit USD amount"
```

Delete a transfer.

```bash
homebudget transfer delete 21007 --yes
```

## Batch commands

The batch command accepts a JSON file list of CRUD operations on transactions (expense, income, transfer).

Command

```bash
homebudget batch run --file operations.json
```

Run with stop-on-error mode.

```bash
homebudget batch run --file operations.json --stop-on-error
```

Run with error report output.

```bash
homebudget batch run --file operations.json --error-report batch_errors.json
```

JSON structure

Each entry is a JSON object with these keys.

- `resource` with values expense, income, or transfer
- `operation` with values add, update, or delete
- `parameters` with the same fields used by the single record CLI commands

Example JSON

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
