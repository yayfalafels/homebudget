# HomeBudget wrapper design

## Table of contents

- [Overview](#overview)
- [Scope and sources](#scope-and-sources)
- [Architecture summary](#architecture-summary)
- [Module structure](#module-structure)
- [Methods surface and data objects](#methods-surface-and-data-objects)
- [User configuration](#user-configuration)
- [Schema mapping](#schema-mapping)
- [Idempotency and conflict policy](#idempotency-and-conflict-policy)
- [Sync update design](#sync-update-design)
- [CLI design](#cli-design)
- [Forex input rules](#forex-input-rules)
- [Packaging and repository layout](#packaging-and-repository-layout)
- [Testing and validation strategy](#testing-and-validation-strategy)
- [Rollout plan and success metrics](#rollout-plan-and-success-metrics)
- [Deprecated design files](#deprecated-design-files)

## Overview

This document consolidates the wrapper design steps into a single reference. It captures the methods surface, schema mapping, sync update approach, and validation strategy.

## Scope and sources

Scope

- Wrapper design for SQLite based HomeBudget data
- Expenses and income operations
- Sync update support for Issue 001
- CLI command design and workflow alignment
- UI control for managing HomeBudget application during database operations

Primary sources

- docs/sqlite-schema.md
- docs/sync-update.md
- docs/workflow.md
- docs/test-cases.md
- HomeBudget Windows guide (local reference)
- hb-finances reference implementation (local reference)

Related implementation guides

- docs/user-guide.md
- docs/developer-guide.md
- docs/methods.md

## Architecture summary

- Package name is homebudget with library and CLI interfaces
- HomeBudgetClient is the primary entry point
- Data objects are typed dataclasses for validation and clarity
- Repository layer handles SQLite operations and transactions
- SyncUpdateManager writes sync payloads in the same transaction

## Module structure

```
src/python/homebudget/
  __init__.py
  __version__.py
  client.py
  models.py
  sync.py
  repository.py
  schema.py
  exceptions.py
  persistence.py
  ui_control.py
  cli/
    __init__.py
    main.py
    expense.py
    income.py
    ui.py
    common.py
```

## Methods surface and data objects

Public methods interface

- HomeBudgetClient with context manager support

Account methods

- `get_account_balance(account, query_date)`: Query account balance on a specific date, calculated from most recent reconcile record adjusted through transactions

Transaction data objects

- ExpenseDTO: Validated expense input for persistence
- IncomeDTO: Validated income input for persistence
- TransferDTO: Validated transfer input for persistence with currency normalization
- BalanceRecord: Read-only result object with account balance information at query date

Batch operation data objects

- BatchOperation: Single batch operation for mixed resource workflows
- BatchOperationResult: Result of mixed batch operation run
- BatchResult: Result of single-resource batch operation

Reference data objects

- Account, Category, SubCategory, Currency querying supported

UI Control

- HomeBudgetUIController provides methods to open, close, and check status of the HomeBudget UI
- Client integrates UI control with transactions when enable_ui_control is set
- UI control automatically closes UI before database operations and reopens after

Method list reference

- See docs/methods.md

## User configuration

The wrapper uses a JSON configuration file for database path, sync settings, and forex preferences. For complete configuration documentation, see [Configuration Guide](configuration.md).

**Configuration file location:**
```
%USERPROFILE%\OneDrive\Documents\HomeBudgetData\hb-config.json
```

**Configuration behavior:**

- Client and CLI load config automatically when present
- Explicit `db_path` parameter or `--db` flag overrides config
- Sync is always enabled via CLI to ensure consistency between devices

## Schema mapping

Core tables

- Expense, Income, Transfer, AccountTrans, Account, Category, SubCategory, Currency

Supporting tables

- SyncInfo, SyncUpdate, DeviceInfo, Settings

Mapping highlights

- AccountTrans links transaction tables with transType and transKey
- Currency values are stored as text and parsed to decimal
- Account currency is required for linked transactions

## Idempotency and conflict policy

- Duplicate detection uses composite field matching
- DuplicateError is raised on exact composite match
- No automatic override, user resolves duplicates manually
- Composite fields include date, account, amount, currency, category or name, notes

## Sync update design

- Sync updates are written for create, update, and delete operations
- Payload encoding uses JSON, zlib, and base64
- DeviceInfo provides primary device identity
- Sync updates are written in the same transaction as data writes
- Batch operations perform one sync update step after the batch completes

## CLI design

- Command groups for expense, income, transfer, batch, sync, and ui
- Global options include db path and sync toggle
- UI control commands support managing the HomeBudget application
- Batch operations support CSV/JSON import for single resources and mixed-operation JSON
- Transfer operations support currency normalization layer for flexible user input

## Forex input rules

Forex inputs follow one of three paths: base currency path for expenses/income, base currency or foreign currency path for expenses/income, and transfer path.

### Expenses and Income

**User Input Semantics**

When users specify `--amount`, the semantic meaning depends on the account:

- For base currency accounts (SGD): `--amount` = amount in base currency
- For non-base currency accounts (USD, RUB, etc.): `--amount` = amount in that account's currency

When specifying `--currency-amount`, the user must also provide `--currency` and `--exchange-rate`:

- `--currency`: The foreign currency code
- `--currency-amount`: The amount in that foreign currency
- `--exchange-rate`: The exchange rate from foreign to base currency
- Backend calculates: `base_amount = currency_amount × exchange_rate`

Backend internally supports specifying any currency with currency_amount and exchange_rate, allowing flexible forex conversions even for accounts not in that currency.

Input validation rules:

- Provide amount only: Currency defaults to account currency, currency amount set to amount
- Provide currency, currency amount, and exchange rate: Amount calculated as currency amount times exchange rate
- Do not provide both amount and currency amount

### Transfers

Transfers use a **currency normalization layer** that accepts user currency specifications for either the from_account or to_account, and converts to the backend standard format.

**Backend Storage Format (Constraint)**

The Transfer table enforces a strict constraint:

- `currency`: **Always** equals from_account currency (constraint enforced at backend)
- `currency_amount`: Amount in from_account currency (from_amount)
- `amount`: Amount in to_account currency (to_amount)

**User Input Modes**

Users can specify transfers in three ways:

1. **Amount Only (Inference)**: Provide only `--amount`. System infers currency based on account types:
   - If base currency in either account → amount is in base currency
   - If base in neither account → amount is in from_account currency

2. **From-Currency Explicit**: Provide `--currency` + `--currency-amount` matching from_account
   - Already in backend format → passes through unchanged

3. **To-Currency Explicit**: Provide `--currency` + `--currency-amount` matching to_account
   - Normalized to backend format using inverse forex calculation
   - `from_amount = to_amount / forex_rate` or cross-rate as appropriate

**Normalization Layer Architecture**

The normalization happens in `client.py → _infer_currency_for_transfer()`:

1. Accepts flexible user input (currency can match either account)
2. Validates: currency must match one of the two accounts (not a third currency)
3. If currency matches to_account, calculates inverse to get from_amount
4. Returns TransferDTO in backend format (currency = from_account)
5. Backend validation (`_validate_transfer_currency_constraint`) enforces the constraint

For detailed normalization rules and examples, see [docs/transfer-currency-normalization.md](transfer-currency-normalization.md).

**Transfer Input Semantics Examples**

When specifying `--amount`:

- If base currency is in either account: `--amount` = amount in base currency
- If base currency is in neither account: `--amount` = amount in from_account currency

This provides intuitive behavior: users think in base currency when it's involved, and in local currency otherwise.

**Case 1: Transfer from base (SGD) to foreign (USD)**

- User provides `--amount` in base currency (SGD)
- Backend infers:
  - `currency=SGD` (from_account currency)
  - `currency_amount=amount` (amount in SGD)
  - `amount=amount/rate` (amount in USD)

- AccountTrans:
  - from_account (SGD): `transAmount=currency_amount` (100 SGD)
  - to_account (USD): `transAmount=amount` (74.07 USD)

**Case 2: Transfer from foreign (USD) to base (SGD)**

- User provides `--amount` in base currency (SGD to receive)
- Backend infers:
  - `currency=USD` (from_account currency)
  - `currency_amount=amount/rate` (amount in USD)
  - `amount=amount` (amount in SGD)

- AccountTrans:
  - from_account (USD): `transAmount=currency_amount` (74.07 USD)
  - to_account (SGD): `transAmount=amount` (100 SGD)

**Case 3: Transfer between two foreign accounts (USD to EUR)**

- User provides `--amount` in from_account currency (USD to send)
- Backend infers:
  - `currency=USD` (from_account currency)
  - `currency_amount=amount` (amount in USD)
  - `amount=amount × (usd_rate ÷ eur_rate)` (amount in EUR)

- AccountTrans:
  - from_account (USD): `transAmount=currency_amount` (100 USD)
  - to_account (EUR): `transAmount=amount` (90 EUR)

When specifying `--currency-amount` for transfers:

- `--currency` and `--currency-amount` together with `--exchange-rate` required
- `--currency` must match one of the transfer accounts
- Backend derives the missing amounts using cross-rate calculation: `from_amount = to_amount × (from_rate ÷ to_rate)`

CLI and client methods enforce these rules to prevent ambiguous inputs.

## Batch operations design

The wrapper supports two types of batch operations:

### Single-Resource Batch Import

Import multiple transactions of the same type from CSV or JSON files:

- `add_expenses_batch()`, `add_incomes_batch()`, `add_transfers_batch()` methods
- `hb expense batch-import`, `hb income batch-import`, `hb transfer batch-import` CLI commands
- Support CSV and JSON file formats
- Each transaction validated independently before insertion
- Sync optimization: Single SyncUpdate created after batch completes (not per transaction)

### Mixed-Resource Batch Operations

Execute multiple operations across different resources in a single atomic batch:

- `batch()` method accepting list of `BatchOperation` objects
- `hb batch run` CLI command with JSON file input
- Supports add, update, delete operations for expense, income, transfer resources
- Continue-on-error mode (default) or stop-on-error mode
- Returns `BatchOperationResult` with successful and failed operations
- Single SyncUpdate created after batch completes

**Batch Behavior:**

- Each individual transaction insert is atomic
- Sync optimization: Batch operations create one sync entry after completion, not per transaction
- Error handling: By default continues on error and reports failures at end
- Validation: Each record validated same as single-record operations
- Transaction atomicity: Each insert is atomic, but batch as whole may partially succeed

**Example Mixed Batch JSON:**
```json
[
  {
    "resource": "expense",
    "operation": "add",
    "parameters": {
      "date": "2026-02-20",
      "category": "Food (Basic)",
      "subcategory": "Restaurant",
      "amount": 25.50,
      "account": "TWH - Personal"
    }
  },
  {
    "resource": "transfer",
    "operation": "add",
    "parameters": {
      "date": "2026-02-20",
      "from_account": "TWH - Personal",
      "to_account": "TWH IB USD",
      "amount": 100.00
    }
  }
]
```

## Packaging and repository layout

Packaging

- Source layout under src/python/homebudget
- Entry points for homebudget and hb commands

Repository layout highlights

- docs contains design and reference documentation
- tests contains unit and integration tests with fixtures
- reference contains the original wrapper and sample databases

## Testing and validation strategy

Automated tests

- Unit tests for models, schema, exceptions, and helpers
- Integration tests for CRUD and sync flows
- CLI tests for command behaviors

Manual validation

- Sync validation in HomeBudget desktop and mobile apps

Coverage target

- 85 percent line coverage minimum

Pre-release checklist

- Full test suite passes with coverage target
- Manual sync validation recorded as pass
- Workflow validation matches docs/workflow.md
- Package build and install verified
- CLI version command works

## Rollout plan and success metrics

Implementation phases

- Foundation, transaction CRUD, sync integration, CLI, and batch operations

Success metrics

- Full CRUD operations for expenses, income, and transfers
- Sync updates propagate to mobile devices
- Test coverage meets or exceeds target
- CLI commands align with workflows

## Deprecated design files

The following design step files are deprecated after Step 1 is complete. Use this document for ongoing work.

- docs/develop/plan-wrapper-design-step2.md
- docs/develop/plan-wrapper-design-step3.md
- docs/develop/plan-wrapper-design-step4.md
- docs/develop/plan-wrapper-design-step5.md
- docs/develop/plan-wrapper-design-step6.md
- docs/develop/plan-wrapper-design-step7.md
- docs/develop/plan-wrapper-design-step8.md
- docs/develop/plan-wrapper-design-step9.md
- docs/develop/plan-wrapper-design-summary.md
