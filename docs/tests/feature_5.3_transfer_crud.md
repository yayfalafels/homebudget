# Manual test for transfer CRUD

## Table of contents

- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Test procedure](#test-procedure)
- [Results](#results)

## Purpose

User acceptance test to validate transfer create, read, update, and delete operations with sync confirmation in the HomeBudget apps.

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

1. User action: record the current transfer count in the Windows app
2. Automated: add a transfer with the wrapper (uses config database by default)

   ```bash
   homebudget transfer add \
     --date 2026-02-20 \
     --from-account "Bank TWH SGD" \
     --to-account "Wallet" \
     --amount 200.00 \
     --notes "TDD Test Transfer"
   ```
   
   _Note: To use a specific database, add `--db <path_to_your_homebudget.db>`_

3. Automated: verify a new SyncUpdate entry exists

   ```bash
   python tests/manual/verify_syncupdate.py
   ```

4. User action: confirm the new transfer appears in the Windows app
5. User action: wait for sync and confirm the transfer appears in the mobile app
6. Automated: locate the new transfer key using the list command

   ```bash
   homebudget transfer list --limit 5
   ```

7. Automated: update the transfer amount with the wrapper using the new key

   ```bash
   homebudget transfer update KEY \
     --amount 250.00 \
     --notes "TDD Test Transfer updated"
   ```

8. User action: confirm the transfer amount update in the Windows app
9. Automated: delete the transfer with the wrapper using the new key

   ```bash
   homebudget transfer delete KEY --yes
   ```

10. User action: confirm the transfer is removed in the Windows app
11. User action: wait for sync and confirm the deletion in the mobile app
12. Record results and any notes

## Results

- Result status
- Notes
- Timestamp
