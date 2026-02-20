# Test Cases

## Table of contents

- [Overview](#overview)
- [Automated tests](#automated-tests)
- [Manual tests](#manual-tests)

## Overview

This document lists system integration tests, manual tests, and forex rate and inference tests. It describes the test coverage and the new forex test cases in a single place.

## Automated tests

### Unit tests

- Exception types and messages, including DuplicateError, NotFoundError, and validation errors.
- DTO validation for required fields, positive amounts, and allowed value ranges.
- DTO serialization and deserialization for date, decimal, and currency fields.
- Schema constants and table references for core entities such as Expense, Income, Transfer, AccountTrans, and SyncUpdate.

### System integration tests

- Repository connection and account listing, including open and close behavior.
- Expense create, read, update, delete, and list behavior with date filters.
- Expense SyncUpdate payload validation for AddExpense operations and payload keys.
- Income create, read, update, delete, and list behavior with date filters.
- Income forex payload validation for currency and currencyAmount fields.
- Transfer create, read, update, delete, and list behavior with date filters.
- Transfer dual AccountTrans creation for transfer out and transfer in rows.
- Currency matching rules for base and non base account scenarios.
- Positive amount constraints for expense, income, and transfer DTOs.
- SyncUpdate payload structure and required keys for core operations.
- Batch add for expense, income, and transfer DTO collections with success and failure reporting.
- Batch operations with continue on error behavior and stop on error behavior.
- Forex rate fetch writes cache file with timestamp, base, and rates.
- Forex rate fetch uses cache within TTL and returns cached value.
- Forex rate fetch uses stale cache on API failure when cache is expired.
- Forex rate fetch returns fallback rate when no cache exists and API fails.
- Invalid currency code returns a validation error.
- Non base account amount only inference sets currency, currency amount, and exchange rate with amount unset.
- Base account foreign transaction requires currency and currency amount.
- Transfer base to non base amount only calculates currency amount without rounding.

## Manual tests

### Manual test runner inventory

- uat_expense_crud, full expense create, read, update, delete with sync verification.
- uat_income_crud, full income create, read, update, delete with sync verification.
- uat_transfer_crud, full transfer create, read, update, delete with sync verification.
- uat_expense_currency_usd, expense create and delete with foreign currency fields.
- uat_income_currency_usd, income create and delete with foreign currency fields.
- uat_transfer_currency_usd, transfer create and delete with foreign currency fields.
- uat_batch_mixed_operations, mixed batch add, update, delete with sync verification.
- uat_batch_import_csv, CSV batch import with sync verification.
- uat_forex_expense_amount_only, expense on non base account with amount only and inferred rate.
- uat_forex_income_amount_only, income on non base account with amount only and inferred rate.
- uat_forex_transfer_amount_only, transfer from base to non base with amount only and inferred rate.
- uat_forex_base_account_validation, base account foreign transaction missing currency amount.

### Manual procedures

- Expense create, read, update, delete with sync verification in desktop and mobile apps.
- Transfer create, read, update, delete with sync verification in desktop and mobile apps.
- SyncUpdate validation procedure for newly created operations and payload presence.
- Forex expense on non base account with amount only, verify currency fields and base amount in both apps.
- Forex income on non base account with amount only, verify currency fields in both apps.
- Forex transfer from base to non base with amount only, verify currency amount and rate in both apps.
- Base account foreign transaction validation, confirm error and no data written.

