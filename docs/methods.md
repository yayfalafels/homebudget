# HomeBudget wrapper method list

## Table of contents

- [Overview](#overview)
- [Client methods](#client-methods)
- [Sync update methods](#sync-update-methods)
- [Repository methods](#repository-methods)
- [Data transfer objects](#data-transfer-objects)
- [Validation utilities](#validation-utilities)
- [Config utilities](#config-utilities)

## Overview

This document lists the methods planned for the wrapper API. It is a reference for implementation and test planning.

## Client methods

HomeBudgetClient lifecycle
- __init__ with db_path and enable_sync
- close
- __enter__
- __exit__

Expense methods
- add_expense expense returns ExpenseRecord
- get_expense key returns ExpenseRecord
- list_expenses filters returns list of ExpenseRecord
- update_expense key and fields returns ExpenseRecord
- delete_expense key returns None

Income methods
- add_income
- get_income
- list_income
- update_income
- delete_income

Transfer methods
- add_transfer
- get_transfer
- list_transfers
- update_transfer
- delete_transfer

Reference data methods
- list_accounts
- list_categories
- list_currencies

Batch methods
- batch

## Sync update methods

SyncUpdateManager
- create_expense_update
- create_income_update
- create_transfer_update
- encode_payload
- insert_sync_update

## Repository methods

Connection and transaction
- connect
- close
- begin_transaction
- commit
- rollback

Expense data
- insert_expense
- get_expense
- list_expenses
- update_expense
- delete_expense

Income data
- insert_income
- get_income
- list_income
- update_income
- delete_income

Transfer data
- insert_transfer
- get_transfer
- list_transfers
- update_transfer
- delete_transfer

Reference data
- list_accounts
- list_categories
- list_currencies

## Data transfer objects

Transaction data
- ExpenseDTO
- IncomeDTO
- TransferDTO

Reference data
- AccountDTO
- CategoryDTO
- CurrencyDTO

## Validation utilities

- validate_expense_inputs
- validate_income_inputs
- validate_transfer_inputs

## Config utilities

- load_user_config
- resolve_db_path
- default_config_path
