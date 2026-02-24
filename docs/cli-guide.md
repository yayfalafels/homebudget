# HomeBudget CLI Guide

## Table of contents

- [Overview](#overview)
- [Setup](#setup)
- [Configuration](#configuration)
- [Global options](#global-options)
- [Account commands](#account-commands)
- [Category commands](#category-commands)
- [Expense commands](#expense-commands)
- [Income commands](#income-commands)
- [Transfer commands](#transfer-commands)
- [Batch commands](#batch-commands)
- [UI control commands](#ui-control-commands)

## Overview

The HomeBudget CLI provides command-line access to database operations. All write operations (add, update, delete) automatically manage the HomeBudget UI to ensure data consistency.

When sync is enabled (default):

- HomeBudget UI automatically closes before database operations
- Database changes are applied atomically while UI is closed
- HomeBudget UI automatically reopens after operations complete
- This prevents data inconsistency and database locks during updates

## Setup

After setting up the virtual environment and installing dependencies, activate the main environment and run the CLI from the repository root.

```bash
source env/Scripts/activate
```

## Configuration

The CLI uses a configuration file for database path and settings. For complete setup and configuration options, see [Configuration Guide](configuration.md).

**Quick reference:**

- Config location: `%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json`
- Sample: `config/hb-config.json.sample`

**Override config:**

```bash
homebudget --db "C:/path/to/homebudget.db" expense list
```

## Global options

**`--db PATH`**

Override database path instead of using config file.

```bash
homebudget --db "C:/path/to/homebudget.db" expense list
```

**Sync control:**

Sync updates are enabled by default and cannot be disabled via CLI. This ensures consistency between local and remote devices. When a write command is executed, SyncUpdate records are automatically created and the HomeBudget UI is automatically managed to prevent conflicts.

## Account commands

### Balance

Query the account balance on a specific date. The balance is calculated from the most recent reconcile (balance) record, then adjusted forward or backward through transactions to the query date.

**Query today's balance:**

```bash
homebudget account balance --account Wallet
```

**Query balance on a specific date:**

```bash
homebudget account balance --account "TWH - Personal" --date 2026-02-01
```

**Output example:**

```
Account Balance: TWH - Personal
Query Date: 2026-02-01
Balance: 1230.45

Reconcile Date: 2026-01-15
Reconcile Amount: 1000.00
```

**How it works:**

- If the query date matches a reconcile date, the balance equals the reconcile amount
- If the query date is after the reconcile date, the balance is calculated forward: reconcile amount + income and transfer_in amounts - expense and transfer_out amounts
- If the query date is before the reconcile date, the balance is calculated backward by reversing the transaction adjustments from the reconcile date
- Raises an error if the account has no reconcile balance record

## Category commands

### List

Display all expense categories ordered by sequence number.

```bash
homebudget category list
```

**Output example:**

```
Categories:
============================================================
Seq   Name
============================================================
0     Personal Discretionary
1     Social & Entertainment
2     Food (Basic)
3     Transport
4     Utilities
============================================================
```

### Subcategories

Display all subcategories for a given parent category, ordered by sequence number.

```bash
homebudget category subcategories --category "Food (Basic)"
```

**Output example:**

```
Subcategories for 'Food (Basic)':
============================================================
Seq   Name
============================================================
13    Groceries
14    Cheap restaurant
35    Food Court
110   Tingkat
162   meal prep
============================================================
```

**Error handling:**

If the category is not found, a clear error message is displayed:

```bash
homebudget category subcategories --category "NonExistentCategory"
```

Output: `Error: Category not found`

## Expense commands

### Add

Base currency account:

```bash
homebudget expense add \
  --date 2026-02-16 \
  --category Dining \
  --subcategory Restaurant \
  --amount 25.50 \
  --account Wallet \
  --notes "Lunch"
```

Foreign currency:

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

### List

With filters:

```bash
homebudget expense list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28 \
  --account Wallet \
  --limit 50
```

### Get

Retrieve by key:

```bash
homebudget expense get 13074
```

### Update

Base currency:

```bash
homebudget expense update 13074 \
  --amount 27.50 \
  --notes "Lunch with tip"
```

Foreign currency:

```bash
homebudget expense update 13074 \
  --currency EUR \
  --currency-amount 15.00 \
  --exchange-rate 1.08 \
  --notes "Lunch with tip"
```

### Delete

```bash
homebudget expense delete 13074 --yes
```

## Income commands

### Add

Base currency:

```bash
homebudget income add \
  --date 2026-02-28 \
  --name "Salary" \
  --amount 5000.00 \
  --account Bank \
  --notes "February salary"
```

Foreign currency:

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

### List

```bash
homebudget income list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```

### Get

```bash
homebudget income get 14021
```

### Update

Base currency:

```bash
homebudget income update 14021 \
  --notes "Updated notes"
```

Foreign currency:

```bash
homebudget income update 14021 \
  --currency EUR \
  --currency-amount 4500.00 \
  --exchange-rate 1.17 \
  --notes "Updated notes"
```

### Delete

```bash
homebudget income delete 14021 --yes
```

## Transfer commands

Transfers support a currency normalization layer that allows flexible input for mixed-currency transfers. You can specify the amount in either the from_account or to_account currency.

### Add

Same currency:

```bash
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "Bank" \
  --to-account "Wallet" \
  --amount 200.00 \
  --notes "Cash withdrawal"
```

Mixed currency, amount inferred:

```bash
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "TWH - Personal" \
  --to-account "TWH IB USD" \
  --amount 200.00 \
  --notes "Transfer to USD account"
```

Mixed currency, explicit from-currency:

```bash
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "TWH IB USD" \
  --to-account "TWH - Personal" \
  --currency USD \
  --currency-amount 150.00 \
  --exchange-rate 1.35 \
  --notes "Transfer to SGD account"
```

Mixed currency, explicit to-currency (normalized):

```bash
homebudget transfer add \
  --date 2026-02-20 \
  --from-account "TWH IB USD" \
  --to-account "Cash TWH EUR" \
  --currency EUR \
  --currency-amount 90.00 \
  --exchange-rate 0.92 \
  --notes "Transfer to EUR account"
```

### List

```bash
homebudget transfer list \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```

### Get

```bash
homebudget transfer get 21007
```

### Update

```bash
homebudget transfer update 21007 \
  --amount 250.00 \
  --notes "Updated transfer amount"
```

Mixed currency:

```bash
homebudget transfer update 21007 \
  --currency USD \
  --currency-amount 180.00 \
  --exchange-rate 1.35 \
  --notes "Updated with explicit USD amount"
```

### Delete

```bash
homebudget transfer delete 21007 --yes
```

## Batch commands

Execute multiple CRUD operations on transactions via JSON file. Run with default stop-on-error:

```bash
homebudget batch run --file operations.json
```

Run with continue-on-error:

```bash
homebudget batch run --file operations.json --continue-on-error
```

Output error report:

```bash
homebudget batch run --file operations.json --error-report batch_errors.json
```

### JSON structure

Each entry is an object with `resource` (expense, income, transfer), `operation` (add, update, delete), and `parameters` using the same fields as single-record CLI commands.

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

### Start

```bash
homebudget ui start
```

With custom verification settings:

```bash
homebudget ui start --verify-attempts 10 --verify-delay 0.3 --settle-time 3.0
```

### Close

```bash
homebudget ui close
```

Without verification:

```bash
homebudget ui close --no-verify
```

### Refresh

```bash
homebudget ui refresh
```

Without force kill:

```bash
homebudget ui refresh --no-force
```

### Status

```bash
homebudget ui status
```
