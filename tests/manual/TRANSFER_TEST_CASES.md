# Transfer UAT Test Cases - Comprehensive Guide

This document describes the comprehensive batch of transfer UAT test cases added to `tests/manual/manual_tests.json`.

## Test Coverage Overview

**Total Transfer Tests:** 23 test cases covering:
- ✅ 3 **Amount-only inference** scenarios (base→foreign, foreign→base, foreign→foreign)
- ✅ 1 **Same-currency** scenario (no forex needed)
- ✅ 3 **Fully-specified** scenarios (amount + currency_amount + rate)
- ✅ 14 **Invalid/error cases** (over-specification, missing fields, constraint violations, etc.)

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

### 2. Same-Currency Transfer Test

#### `uat_transfer_same_currency_both_sides`
- **From:** TWH - Personal (SGD)
- **To:** TWH Savings (SGD)
- **Input:** `--amount 500.00`
- **Expected:**
  - `currency=SGD`
  - `currency_amount=500` (1:1)
  - `amount=500` (1:1, no forex)
- **Validates:** No forex calculation when currencies match

### 3. Fully-Specified Tests

These test explicit specification of all forex parameters:

#### `uat_transfer_full_spec_base_to_foreign`
- **Command:** `--amount 100.00 --currency SGD --currency-amount 100.00 --exchange-rate 1.35`
- **Expected:**
  - `currency=SGD`
  - `currency_amount=100`
  - `amount≈74` (100/1.35)
- **Validates:** User can override inference with explicit values

#### `uat_transfer_full_spec_foreign_to_base`
- **Command:** `--currency-amount 75.00 --currency USD --amount 100.00 --exchange-rate 1.35`
- **Expected:**
  - `currency=USD`
  - `currency_amount=75`
  - `amount=100`
- **Validates:** Full specification for foreign→base

#### `uat_transfer_full_spec_foreign_to_foreign`
- **Command:** `--currency-amount 120.00 --currency USD --amount 110.00 --exchange-rate 1.35`
- **Expected:**
  - `currency=USD`
  - `currency_amount=120`
  - `amount=110`
- **Validates:** Full specification for foreign→foreign

## Invalid Test Scenarios

These validate error handling and constraint enforcement:

### Over-Specification Errors

#### `uat_transfer_invalid_amount_and_currency_amount`
- **Input:** Both `--amount 100.00` and `--currency-amount 75.00` (no rate)
- **Expected:** ❌ Error - ambiguous specification
- **Validates:** Cannot specify both amount types without exchange_rate

### Missing Required Fields

#### `uat_transfer_invalid_currency_amount_no_currency`
- **Input:** `--currency-amount 75.00 --exchange-rate 1.35` (no `--currency`)
- **Expected:** ❌ Error - currency required when currency_amount specified
- **Validates:** currency_amount requires currency field

#### `uat_transfer_invalid_currency_amount_no_rate`
- **Input:** `--currency SGD --currency-amount 100.00` (no `--exchange-rate`)
- **Expected:** ❌ Error - rate required when currency_amount specified
- **Validates:** currency_amount requires exchange_rate

#### `uat_transfer_invalid_missing_amount`
- **Input:** No `--amount` or `--currency-amount`
- **Expected:** ❌ Error - at least one must be specified
- **Validates:** Amount is mandatory

### Currency Constraint Violations

#### `uat_transfer_invalid_third_currency`
- **Transfer:** SGD→USD with `--currency EUR`
- **Expected:** ❌ Error - currency must match from_account or to_account
- **Validates:** Currency constraint enforcement (cannot be 3rd currency)

#### `uat_transfer_invalid_currency_not_from_account`
- **Transfer:** SGD→USD with `--currency USD`
- **Expected:** ❌ Error - currency must match from_account (SGD)
- **Validates:** Currency must match from_account, not to_account

### Value Constraint Violations

#### `uat_transfer_invalid_negative_amount`
- **Input:** `--amount -100.00`
- **Expected:** ❌ Error - amount must be positive
- **Validates:** Positive amount constraint

#### `uat_transfer_invalid_zero_amount`
- **Input:** `--amount 0.00`
- **Expected:** ❌ Error - amount must be positive
- **Validates:** Amount must be non-zero

#### `uat_transfer_invalid_negative_currency_amount`
- **Input:** `--currency-amount -100.00`
- **Expected:** ❌ Error - currency_amount must be positive
- **Validates:** Positive currency_amount constraint

#### `uat_transfer_invalid_zero_exchange_rate`
- **Input:** `--exchange-rate 0.00`
- **Expected:** ❌ Error - rate must be positive
- **Validates:** Exchange rate must be positive

#### `uat_transfer_invalid_negative_exchange_rate`
- **Input:** `--exchange-rate -1.35`
- **Expected:** ❌ Error - rate must be positive
- **Validates:** Exchange rate must be positive

### Account Validation Errors

#### `uat_transfer_invalid_nonexistent_account`
- **Input:** `--from-account "Nonexistent Account"`
- **Expected:** ❌ Error - account not found
- **Validates:** Account existence validation

#### `uat_transfer_invalid_same_account`
- **Input:** `--from-account "TWH - Personal" --to-account "TWH - Personal"`
- **Expected:** ❌ Error - from and to accounts must differ
- **Validates:** Cannot transfer to same account

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

# Full-spec tests
python tests/manual/manual_test_runner.py --test-id uat_transfer_full_spec_base_to_foreign
python tests/manual/manual_test_runner.py --test-id uat_transfer_full_spec_foreign_to_base
python tests/manual/manual_test_runner.py --test-id uat_transfer_full_spec_foreign_to_foreign

# Invalid tests
python tests/manual/manual_test_runner.py --test-id uat_transfer_invalid_amount_and_currency_amount
# ... etc
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
  - `TWH Savings` (SGD base) - for same-currency test
  - `TWH IB USD` (USD foreign)
  - `TWH EUR` (EUR foreign) - for foreign-to-foreign tests
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
