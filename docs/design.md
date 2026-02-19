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

Forex inputs follow one of two paths for expenses and income.

Base currency path
- Provide amount only
- Currency defaults to the account currency
- Currency amount is set to amount for base currency updates
- Exchange rate is treated as 1.0

Foreign currency path
- Provide currency, currency amount, and exchange rate
- Amount is calculated as currency amount times exchange rate

Do not provide amount and currency amount together, except when they are equal for base currency updates.

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
