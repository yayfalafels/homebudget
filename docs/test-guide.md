# Test Guide

## Table of Contents

- [Related documents](#related-documents)
- [Overview](#overview)
- [Test Types](#test-types)
- [Prerequisites](#prerequisites)
- [Running Tests](#running-tests)
- [UAT Test Workflow](#uat-test-workflow)
- [Feature Coverage](#feature-coverage)
- [Troubleshooting](#troubleshooting)
- [Test Development](#test-development)
- [Continuous Integration](#continuous-integration)

## Related documents

- [Developer Guide](developer-guide.md) - Development setup
- [Environment Documentation](develop/environment.md) - Python environment
- [Implementation Plan](../.github/prompts/plan-wrapper-implementation.prompt.md) - Feature implementation phases
- [Sync Mechanism](sync-update.md) - SyncUpdate details
- [SQLite Schema](sqlite-schema.md) - Database structure

## Overview

This guide covers how to run tests for the HomeBudget Wrapper, including unit tests, manual tests — SIT — and User Acceptance Tests — UAT.

## Test Types

### Unit Tests
Automated tests for Python code modules and functions.

### System Integration Tests (SIT)
Manual tests that verify wrapper functionality without involving mobile devices.

### User Acceptance Tests (UAT)
Manual tests that verify complete CRUD workflows with sync validation across desktop and mobile devices.

---

## Prerequisites

### For All Tests
- Python 3.12+
- Wrapper installed in editable mode: `pip install -e .`
- Development environment configured: See [environment.md](develop/environment.md)

### For Manual Tests — SIT and UAT
- **hb-config.json** configured with correct database path
  - Location: `~/.homebudget/hb-config.json` on first run, or specify via environment
  - See [developer-guide.md](developer-guide.md#configuration) for setup
- **Database**: HomeBudget.db with test data
- **Test resources must exist**: 
  - Account: "TWH - Personal"
  - Account: "30 CC Hashemis" for transfers
  - Category: "Food (Basic)"
  - Category: "Salary and Wages" for income
  - Subcategory under Food: "Cheap restaurant"

### UAT Tests — Mobile Verification
- Mobile device with HomeBudget app installed
- Mobile device on WiFi network
- Mobile app signed in with same account as desktop
- Easy access to mobile device to verify sync results

---

## Running Tests

### Unit Tests

Run all unit tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src/python/homebudget
```

Run specific test file:
```bash
pytest tests/unit/test_models.py
```

---

### Manual Tests (System Integration Testing)

Manual tests verify wrapper functionality interactively. The test runner automates CLI operations and prompts you to verify UI changes.

#### List Available SIT Tests

```bash
python tests/manual/manual_test_runner.py --list
```

Output shows available test IDs and descriptions.

#### Run a Specific SIT Test

```bash
python tests/manual/manual_test_runner.py --test-id <test_id>
```

Example:
```bash
python tests/manual/manual_test_runner.py --test-id sync_validation
```

#### Run Tests Interactively

If no `--test-id` specified, the runner shows a menu:
```bash
python tests/manual/manual_test_runner.py
```

#### Results

Results are saved to `tests/manual/results/<test-id>-<timestamp>.md` with:
- Test summary (overall pass/fail/incomplete)
- Step-by-step results with commands, outputs, and notes
- Timestamps for each test run

View latest result:
```bash
ls -t tests/manual/results/*.md | head -1
```

---

### UAT Tests — Full CRUD with Mobile Sync

UAT tests verify complete Create-Read-Update-Delete workflows with mobile synchronization. These tests require manual verification that changes sync to mobile devices.

#### Available UAT Tests

```bash
python tests/manual/manual_test_runner.py --list
```

Three main UAT tests:
- `uat_expense_crud` - Expense full CRUD with sync validation
- `uat_income_crud` - Income full CRUD with sync validation
- `uat_transfer_crud` - Transfer full CRUD with sync validation

#### Run Single UAT Test

```bash
python tests/manual/manual_test_runner.py --test-id uat_expense_crud
```

This will:
1. Verify configuration is ready — you confirm
2. Create a test expense via CLI — automated
3. Verify SyncUpdate entry created — automated
4. Ask you to verify expense appears in Windows AND mobile apps — manual
5. List expenses and ask you to record the key — interactive
6. Read the expense — automated
7. Update the expense — automated
8. Verify sync — manual
9. Delete the expense — automated
10. Verify sync — manual

#### Run All UAT Tests Sequentially

To run all UAT tests in order — expense, income, then transfer:

```bash
python tests/manual/manual_test_runner.py --test-id uat_expense_crud
python tests/manual/manual_test_runner.py --test-id uat_income_crud
python tests/manual/manual_test_runner.py --test-id uat_transfer_crud
```

Or use a loop:
```bash
for test in uat_expense_crud uat_income_crud uat_transfer_crud; do
  python tests/manual/manual_test_runner.py --test-id $test
done
```

#### Specifying Output Directory

```bash
python tests/manual/manual_test_runner.py --test-id uat_expense_crud \
  --output-dir .dev/uat-results
```

#### Reference Data Testing

Reference data tests verify read-only queries for accounts, categories, currencies, and other lookup tables. These are automated unit tests without mobile sync verification.

**Run reference data tests:**
```bash
pytest tests/unit/test_reference_data.py -v
```

Tests verify:
- Query all accounts and return correct structure
- Filter accounts by type or status
- List all categories with hierarchy
- Filter categories by parent
- Query currencies by code or name

#### Batch Operations Testing

Batch operations tests verify importing multiple transactions from CSV or JSON files, with sync optimizations and error handling.

**Run batch operation tests:**

Automated tests:
```bash
pytest tests/integration/test_batch_operations.py -v
```

Manual test with real data:
```bash
python tests/manual/manual_test_runner.py --test-id sit_batch_import_csv
```

**Batch operation capabilities:**
- File formats: CSV with headers or JSON array of transaction objects
- Large files: Tested with 100 plus rows
- Individual input validation per record
- Sync disabled during individual processing, single sync after batch
- Result summary with success/failure counts

**Example batch commands:**
```bash
# Import expenses from CSV
homebudget expense batch-import --file expenses.csv --format csv

# Import income from JSON
homebudget income batch-import --file income.json --format json

# Import transfers with error reporting
homebudget transfer batch-import --file transfers.csv --format csv --error-report errors.txt
```

#### UAT Batch Import with Mobile Sync

UAT batch testing validates that imported transactions sync correctly to mobile devices. This follows the same sync validation pattern as individual CRUD operations but for bulk imports.

**Run UAT batch test:**
```bash
python tests/manual/manual_test_runner.py --test-id uat_batch_import_csv
```

**Test workflow:**
1. **Setup** — Note expense count in Windows and mobile apps
2. **Import** — Batch import 20 expenses from CSV via CLI (automated)
3. **Verify Import** — Check CLI summary shows 20 successful (automated)
4. **Verify Desktop** — Confirm all 20 expenses appear in Windows app (manual)
5. **Verify Mobile** — Wait 30 seconds for sync and verify on mobile (manual)
6. **Check Totals** — Verify transaction count increased by exactly 20 (manual)

**Expected result:** All 20 batch-imported transactions appear in both Windows and mobile apps with correct amounts, categories, and dates.

---

## UAT Test Workflow

Each UAT test follows this pattern:

### 1. Setup — Manual
- Confirm hb-config.json is configured
- Ensure mobile device is connected to WiFi
- Note current transaction counts in both apps

### 2. Create — Automated then Manual Verification
```
CLI Creates transaction → SyncUpdate inserted → Verify both apps updated
```
- Wrapper CLI creates resource, which can be an expense, income, or transfer
- Test runner verifies SyncUpdate entry exists
- **You verify**: New transaction appears in Windows app AND mobile app

### 3. Read — Automated
- List transactions and record the resource key
- CLI retrieves transaction details
- **You verify**: Details match what was entered

### 4. Update — Automated then Manual Verification
```
CLI Updates amount/notes → SyncUpdate inserted → Verify both apps updated
```
- CLI updates transaction
- Test runner verifies SyncUpdate entry exists
- **You verify**: Updated transaction appears in Windows app AND mobile app

### 5. Delete — Automated then Manual Verification
```
CLI Deletes transaction → SyncUpdate inserted → Verify removed from both apps
```
- CLI deletes transaction
- Test runner verifies SyncUpdate entry exists
- **You verify**: Transaction removed from Windows app AND mobile app

---

## Feature Coverage

The test suite covers all planned features from the implementation plan:

| Feature | Testing Type | Status | Entry Point |
| --- | --- | --- | --- |
| 5.1 Expense CRUD | UAT plus automated | Enabled | `uat_expense_crud` test |
| 5.2 Income CRUD | UAT plus automated | Enabled | `uat_income_crud` test |
| 5.3 Transfer CRUD | UAT plus automated | Enabled | `uat_transfer_crud` test |
| 5.4 Reference Data | Automated only | Enabled | `pytest tests/unit/test_reference_data.py` |
| 5.5 CLI Commands | Automated plus manual | Enabled | UAT tests use CLI, SIT can target specific commands |
| 5.6 Batch Operations | UAT plus automated | Enabled | `uat_batch_import_csv` test, `pytest tests/integration/test_batch_operations.py` |

**Test automation levels:**
- **Automated only**: Unit tests run without user interaction or mobile devices
- **Automated plus manual**: Automated tests verify code paths, manual tests verify UI in HomeBudget on Windows and mobile
- **UAT**: Full workflow including sync validation on mobile devices

---

## Troubleshooting

### Test Runner Issues

#### "No SyncUpdate entries found"
- Ensure database path in hb-config.json is correct
- Verify sync is enabled in config
- Check that CLI commands executed successfully

#### "Account not found" or "Category not found"
- Verify required test resources exist in database
- Check exact account/category names match — names are case-sensitive
- See prerequisites section above

#### "Command timeout"
- Increase timeout in `manual_test_runner.py` — default is 30 seconds
- Check that CLI commands work manually
- Verify database is accessible

### Sync Verification Issues

#### Expense doesn't appear on mobile
1. Check WiFi connectivity on both devices
2. Verify both devices signed in with same account
3. Check SyncUpdate entry in database: `python tests/manual/verify_syncupdate.py`
4. Check mobile app logs or wait longer for sync
5. Verify device registration in DeviceInfo table

#### Mobile shows transaction but desktop shows error
- Desktop transaction may have failed silently
- Check wrapper logs for errors
- Verify all required fields were populated
- Check database for partial transaction

---

## Test Development

### Adding New UAT Tests

Edit `tests/manual/manual_tests.json` and add a new test object:

```json
{
  "id": "uat_myresource_crud",
  "title": "UAT: MyResource CRUD with sync validation",
  "resource": "myresource",
  "steps": [
    {
      "kind": "user",
      "label": "Record count and verify mobile is on WiFi"
    },
    {
      "kind": "auto",
      "label": "Create test resource",
      "command": "homebudget <resource> add --param value ..."
    },
    ...
  ]
}
```

### Step Types

- `"kind": "auto"`: CLI command executed automatically
  - `"command"`: Shell command to run
  - `"command_template"`: Command with placeholders like `{expense_key}`
- `"kind": "user"`: Manual verification step
  - Prompts user for pass/fail/skip and optional notes
  - Can capture variables such as transaction key for use in later steps

### Adding Batch Operation Tests

For UAT batch operations with mobile sync validation, add test with CSV and JSON file handling:

```json
{
  "id": "uat_batch_import_expenses",
  "title": "UAT: Batch import expenses from CSV with mobile sync validation",
  "resource": "batch",
  "steps": [
    {
      "kind": "user",
      "label": "Record current expense count in Windows and mobile apps, ensure mobile is on WiFi"
    },
    {
      "kind": "auto",
      "label": "Import 20 expenses from CSV",
      "command": "homebudget expense batch-import --file tests/fixtures/test_expenses.csv --format csv"
    },
    {
      "kind": "auto",
      "label": "Verify import summary shows 20 successful",
      "command": "python tests/manual/verify_batch_import.py --count 20"
    },
    {
      "kind": "user",
      "label": "Verify: All 20 expenses appear in Windows app with correct amounts and categories"
    },
    {
      "kind": "user",
      "label": "Wait 30 seconds for sync, verify all 20 expenses appear on mobile device"
    },
    {
      "kind": "user",
      "label": "Verify: Transaction count increased by exactly 20 on both Windows and mobile"
    }
  ]
}
```

---

## Continuous Integration

For CI/CD pipelines, unit tests can run automatically:

```bash
pytest --cov=src/python/homebudget --tb=short
```

Manual tests — both SIT and UAT — require human interaction and should be run locally before commits.

---

