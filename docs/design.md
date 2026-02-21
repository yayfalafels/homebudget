# HomeBudget wrapper design

## Table of contents

- [Overview](#overview)
- [Scope and sources](#scope-and-sources)
- [Architecture summary](#architecture-summary)
- [Module structure](#module-structure)
- [API surface and data objects](#api-surface-and-data-objects)
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

This document consolidates the wrapper design steps into a single reference. It captures the API surface, schema mapping, sync update approach, and validation strategy.

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
- reference/HomeBudget_Windows_guide.md
- reference/hb-finances

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

## API surface and data objects

Public API entry point
- HomeBudgetClient with context manager support

Transaction data objects
- ExpenseDTO
- IncomeDTO
- TransferDTO (defined but not yet implemented)

Reference data objects
- Not yet implemented

Batch operations
- Not yet implemented

UI Control
- HomeBudgetUIController provides methods to open, close, and check status of the HomeBudget UI
- Client integrates UI control with transactions when enable_ui_control is set
- UI control automatically closes UI before database operations and reopens after

Method list reference
- See docs/methods.md

## User configuration

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

Client and CLI behavior
- HomeBudgetClient uses db_path from config when not provided
- CLI uses db_path from config when --db is not provided

## Schema mapping

Core tables
- Expense, Income, Transfer (transfer not yet implemented), AccountTrans, Account, Category, SubCategory, Currency

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

- Command groups for expense, income, and ui
- Global options include db path and sync toggle
- UI control commands support managing the HomeBudget application

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

Transfers follow the constraint: **currency and currency_amount must match the from_account**.

**Transfer Table Fields**

The Transfer table fields represent:
- `currency`: Always matches from_account currency (constraint enforced)
- `currency_amount`: Amount in from_account currency
- `amount`: Amount in to_account currency

**User Input Semantics for Transfers**

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
