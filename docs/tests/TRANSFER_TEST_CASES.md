# Transfer UAT Test Cases - Comprehensive Guide

This document describes the comprehensive batch of transfer UAT test cases added to `tests/manual/manual_tests.json`.

## Test Coverage Overview

**Total Transfer Tests:** 6 test cases covering:
- ✅ 3 **Amount-only inference** scenarios (base→foreign, foreign→base, foreign→foreign)
- ✅ 3 **Batch transfer** scenarios (valid transfers and multiple items with error handling)

## Valid Test Scenarios

### 1. Amount-Only Inference Tests

These test the automatic currency inference based on account currencies:

#### `uat_transfer_amount_only_base_to_foreign`
- **From:** TWH - Personal (SGD base)
- **To:** TWH IB USD (USD foreign)
- **Input:** `--amount 250.00`
- **Expected:**
  - `currency=SGD` (from_account currency)
  - `currency_amount=250` (from_account amount)
  - `amount≈185` (to_account amount = 250/1.35)
- **Validates:** Base→Foreign conversion with inferred currency_amount

#### `uat_transfer_amount_only_foreign_to_base`
- **From:** TWH IB USD (USD foreign)
- **To:** TWH - Personal (SGD base)
- **Input:** `--amount 300.00` (amount to receive in base)
- **Expected:**
  - `currency=USD` (from_account currency)
  - `currency_amount≈222` (from_account amount = 300/1.35)
  - `amount=300` (to_account amount)
- **Validates:** Foreign→Base conversion with inferred currency_amount

#### `uat_transfer_amount_only_foreign_to_foreign`
- **From:** TWH IB USD (USD foreign)
- **To:** TWH EUR (EUR foreign)
- **Input:** `--amount 150.00` (amount in from_currency)
- **Expected:**
  - `currency=USD` (from_account currency)
  - `currency_amount=150` (from_account amount)
  - `amount` calculated using cross-rate (USD/EUR)
- **Validates:** Foreign→Foreign conversion with cross-rate calculation

## Running the Tests

### Run All Transfer Tests
```bash
python tests/manual/manual_test_runner.py --test-id uat_transfer_amount_only_base_to_foreign
```

### Run Specific Test Category
```bash
# Amount-only tests
python tests/manual/manual_test_runner.py --test-id uat_transfer_amount_only_base_to_foreign
python tests/manual/manual_test_runner.py --test-id uat_transfer_amount_only_foreign_to_base
python tests/manual/manual_test_runner.py --test-id uat_transfer_amount_only_foreign_to_foreign

# Batch transfer tests
python tests/manual/manual_test_runner.py --test-id uat_batch_transfer_valid
python tests/manual/manual_test_runner.py --test-id uat_batch_transfer_invalid
```

### Run All Transfer Tests (Batch)
```bash
# Use the UAT runner to execute all transfer tests
python tests/manual/run_uat_tests.py | grep transfer
```

## Key Validation Points for Manual Testing

### For Valid Transfers
1. ✅ Verify SyncUpdate is created for each transfer
2. ✅ Verify transfer appears in Windows app and mobile app
3. ✅ Verify currency and currency_amount are correct in app display
4. ✅ Verify from_account and to_account amounts are different for cross-currency
5. ✅ Verify from_account and to_account amounts are equal for same-currency
6. ✅ Verify delete creates SyncUpdate and removes from both apps

### For Invalid Transfers
1. ✅ Verify appropriate error message is shown
2. ✅ Verify no transfer is created in database
3. ✅ Verify no SyncUpdate is created
4. ✅ Verify app remains consistent (no orphaned data)

## Test Execution Dependencies

**Prerequisites for running full test suite:**
- Database must have accounts:
  - `TWH - Personal` (SGD base)
  - `TWH IB USD` (USD foreign)
  - Forex rates available for USD/SGD and EUR conversions

**Prerequisites for sync validation:**
- Mobile app configured and on same WiFi network
- Mobile app synced before running tests
- API server accessible for SyncUpdate updates

## Coverage Matrix

| Test Scenario | Base→Foreign | Foreign→Base | Foreign→Foreign | Same Currency |
|---|:---:|:---:|:---:|:---:|
| Amount only | ✅ | ✅ | ✅ | ✅ |
| Full spec | ✅ | ✅ | ✅ | N/A |
| Invalid: Over-spec | ✅ | ✅ | ✅ | ✅ |
| Invalid: Missing field | ✅ | ✅ | ✅ | ✅ |
| Invalid: 3rd currency | ✅ | ✅ | ✅ | N/A |
| Invalid: Wrong currency | ✅ | ✅ | ✅ | N/A |
| Invalid: Negative amount | ✅ | ✅ | ✅ | ✅ |
| Invalid: Zero amount | ✅ | ✅ | ✅ | ✅ |
| Invalid: Bad rate | ✅ | ✅ | ✅ | N/A |
| Invalid: Account constraints | ✅ | ✅ | ✅ | ✅ |

## Maintenance Notes

When updating transfer business logic:
1. Add corresponding test case if new feature/scenario
2. Update invalid test cases if validation rules change
3. Update expected values if forex conversion logic changes
4. Document any new test prerequisites
5. Verify all existing tests still pass after changes
