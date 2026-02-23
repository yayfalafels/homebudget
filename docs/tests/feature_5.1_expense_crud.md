# Manual test for expense CRUD

## Table of contents

- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Test procedure](#test-procedure)
- [Results](#results)

## Purpose

User acceptance test to validate expense create, read, update, and delete operations with sync confirmation in the HomeBudget apps.

## Prerequisites

- HomeBudget Windows app installed and running
- HomeBudget mobile app available for sync checks
- Live HomeBudget database configured and connected to the apps
  - Copy `config/hb-config.json.sample` to `%USERPROFILE%/OneDrive/Documents/HomeBudgetData/hb-config.json`
  - Edit the config file to set `db_path` to your operational homebudget.db
  - Or use `--db` flag to specify your operational database path

- Wrapper environment activated
- Package installed in editable mode

## Test procedure

1. User action: record the current expense count in the Windows app
2. Automated: add an expense with the wrapper (uses config database by default)

   ```bash
   homebudget expense add \
     --date 2026-02-16 \
     --category Dining \
     --subcategory Restaurant \
     --amount 25.50 \
     --account Wallet \
     --notes "TDD Test Expense"
   ```
   
   _Note: To use a specific database, add `--db <path_to_your_homebudget.db>`_

3. Automated: verify a new SyncUpdate entry exists

   ```bash
   python tests/manual/verify_syncupdate.py
   ```

4. User action: confirm the new expense appears in the Windows app
5. User action: wait for sync and confirm the expense appears in the mobile app
6. Automated: locate the new expense key using the list command

   ```bash
   homebudget expense list --limit 5
   ```

7. Automated: update the expense amount with the wrapper using the new key

   ```bash
   homebudget expense update KEY \
     --amount 27.50 \
     --notes "TDD Test Expense updated"
   ```

8. User action: confirm the expense amount update in the Windows app
9. Automated: delete the expense with the wrapper using the new key

   ```bash
   homebudget expense delete KEY --yes
   ```

10. User action: confirm the expense is removed in the Windows app
11. User action: wait for sync and confirm the deletion in the mobile app
12. Record results and any notes

## Results

- Result status
- Notes
- Timestamp
