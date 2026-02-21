# Batch Transfer UAT Test Cases

This document describes the batch transfer UAT test cases using the `hb transfer batch-import` command.

## Overview

Two comprehensive batch transfer test cases have been added to test the batch import functionality with JSON input:

1. **`uat_batch_transfer_valid`** - Batch import with 11 items: 10 valid transfers covering all scenarios (inferred, explicit from-currency, explicit to-currency) + 1 with parsing error to verify error reporting
2. **`uat_batch_transfer_invalid`** - Batch import with mixed valid/invalid transfers to test error handling (including over-specified case)

## Currency Normalization Layer

The implementation includes a normalization layer that accepts user currency specifications for **either** the from_account OR to_account, and converts them to the backend standard format (currency = from_account, currency_amount = from_amount).

**User Input Modes:**
1. **Amount only**: System infers currency based on account types (base currency if present)
2. **From-currency explicit**: `currency` + `currency_amount` matching from_account (pass through)
3. **To-currency explicit**: `currency` + `currency_amount` matching to_account (normalized to from-currency format)

**Backend Storage Format:**
- `currency`: Always equals from_account currency
- `currency_amount`: Amount in from_account currency
- `amount`: Amount in to_account currency

## Test Case 1: uat_batch_transfer_valid

### Purpose
Validate that batch import correctly creates multiple transfers with different currency scenarios and properly syncs to mobile app. Tests:
- Inferred currency (amount only)
- Explicit from-currency specification (currency matches from_account)
- **Explicit to-currency specification (currency matches to_account) - tests normalization layer**
- Parsing error reporting (not silently dropped)

### Input: `transfers_valid_batch.json`
11 items in single batch (10 valid + 1 parsing error):

**Items 1-4: Amount Only (Currency Inferred)**
```json
  {
    "date": "2026-02-22",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "amount": "200.00",
    "notes": "UAT Batch: SGD->USD Amount Only"
  },
  {
    "date": "2026-02-22",
    "from_account": "TWH IB USD",
    "to_account": "TWH - Personal",
    "amount": "400.00",
    "notes": "UAT Batch: USD->SGD Amount Only"
  },
  {
    "date": "2026-02-22",
    "from_account": "TWH IB USD",
    "to_account": "Cash TWH EUR",
    "amount": "180.00",
    "notes": "UAT Batch: USD->EUR Amount Only"
  },
  {
    "date": "2026-02-22",
    "from_account": "TWH - Personal",
    "to_account": "30 CC Hashemis",
    "amount": "600.00",
    "notes": "UAT Batch: SGD->SGD Same Currency"
  }
```

**Items 5-7: Explicit From-Currency (Pass Through)**
```json
  {
    "date": "2026-02-22",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "currency": "SGD",
    "currency_amount": "250.00",
    "notes": "UAT Batch: SGD->USD Explicit From Currency (Base)"
  },
  {
    "date": "2026-02-22",
    "from_account": "TWH IB USD",
    "to_account": "TWH - Personal",
    "currency": "USD",
    "currency_amount": "150.00",
    "notes": "UAT Batch: USD->SGD Explicit From Currency (Non-Base)"
  },
  {
    "date": "2026-02-22",
    "from_account": "TWH IB USD",
    "to_account": "Cash TWH EUR",
    "currency": "USD",
    "currency_amount": "120.00",
    "notes": "UAT Batch: USD->EUR Explicit From Currency (Non-Base)"
  }
```

**Items 8-10: Explicit To-Currency (Normalized to From-Currency)**
```json
  {
    "date": "2026-02-22",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "currency": "USD",
    "currency_amount": "100.00",
    "notes": "UAT Batch: SGD->USD Explicit To Currency (Non-Base) [NORMALIZED]"
  },
  {
    "date": "2026-02-22",
    "from_account": "TWH IB USD",
    "to_account": "TWH - Personal",
    "currency": "SGD",
    "currency_amount": "300.00",
    "notes": "UAT Batch: USD->SGD Explicit To Currency (Base) [NORMALIZED]"
  },
  {
    "date": "2026-02-22",
    "from_account": "Cash TWH EUR",
    "to_account": "TWH IB USD",
    "currency": "USD",
    "currency_amount": "90.00",
    "notes": "UAT Batch: EUR->USD Explicit To Currency (Non-Base) [NORMALIZED]"
  }
```

**Item 11: Parsing Error (Invalid Date)**
```json
  {
    "date": "2026-22-02",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "amount": "100.00",
    "notes": "UAT Batch: INVALID DATE FORMAT (should cause parsing error)"
  }
```

### Expected Results

**Command Output:**
```
1 parsing error(s) occurred:
  Item 11: time data '2026-22-02' does not match format '%Y-%m-%d'

Batch import completed
  Successful: 10
  Failed: 0
```

**Parsing Errors:**
- ❌ **Item 8:** Invalid date format (2026-22-02) - demonstrates that parsing errors are now reported instead of being silently dropped

**Item 1: Base→Foreign (SGD→USD) - Amount Only**
- ✅ Created
- `currency=SGD` (from_account)
- `currency_amount=200` (in SGD)
- `amount≈148` (in USD, 200/1.35)

**Item 2: Foreign→Base (USD→SGD) - Amount Only**
- ✅ Created
- `currency=USD` (from_account)
- `currency_amount≈296` (in USD, 400/1.35)
- `amount=400` (in SGD)

**Item 3: Foreign→Foreign (USD→EUR) - Amount Only**
- ✅ Created
- `currency=USD` (from_account)
- `currency_amount=180` (in USD)
- `amount` calculated using cross-rate

**Item 4: Same Currency (SGD→SGD)**
- ✅ Created
- `currency=SGD`
- `currency_amount=600` (1:1)
- `amount=600` (1:1, no forex)

**Item 5: Base→Foreign (SGD→USD) - Explicit From Currency**
- ✅ Created
- `currency=SGD` (explicitly specified, matches from_account)
- `currency_amount=250` (in SGD, explicitly specified)
- `amount≈185` (in USD, calculated: 250/1.35)

**Item 6: Foreign→Base (USD→SGD) - Explicit From Currency**
- ✅ Created
- `currency=USD` (explicitly specified, matches from_account)
- `currency_amount=150` (in USD, explicitly specified)
- `amount≈202.50` (in SGD, calculated: 150*1.35)

**Item 7: Foreign→Foreign (USD→EUR) - Explicit From Currency**
- ✅ Created
- `currency=USD` (explicitly specified, matches from_account)
- `currency_amount=120` (in USD, explicitly specified)
- `amount` calculated using cross-rate (USD→SGD→EUR)

### Sync Validation
- ✅ 10 SyncUpdate records created (1 item failed parsing, doesn't reach processing)
- ✅ All 10 transfers visible in Windows app
- ✅ All 10 transfers visible in mobile app (with correct currencies)
- ✅ Amounts reflect correct currency conversions in UI
- ✅ Inferred (Items 1-4), explicit from-currency (Items 5-7), and explicit to-currency (Items 8-10) specifications all work correctly
- ✅ **To-currency specifications (Items 8-10) are normalized to backend format (currency = from_account)**
- ✅ Parsing errors are displayed (Item 11 shows error, not silently dropped)

### Test Workflow
The test follows a streamlined workflow that doesn't enumerate each transfer case individually:

1. Import batch of 11 items (10 valid + 1 parsing error)
2. **Verify parsing error displayed** for Item 11 (invalid date format)
3. List all transfers (shows keys, amounts, accounts - should show 10 transfers)
4. **Record transfer keys** from the list (comma-separated) - **Important: Choose "pass" to trigger key recording prompt**
5. Verify all 10 transfers appear in apps with correct data
6. **Verify to-currency items (8-10) were normalized correctly** - check database shows currency = from_account
7. Verify SyncUpdates created for 10 transfers
8. **Automated rollback** using recorded keys

**Note:** The test is generic and adapts to whatever transfers are defined in `transfers_valid_batch.json`. Adding or removing test cases updates the batch automatically without changing the test workflow.

### Rollback
- Automated rollback using batch delete with recorded transfer keys
- The rollback step uses the `rollback_transfers.json` template which expands `{TRANSFER_KEYS}` to individual delete operations

---

## Test Case 2: uat_batch_transfer_invalid

### Purpose
Validate that batch import correctly handles mixed valid/invalid transfers with `continue_on_error` behavior, reporting specific errors for each invalid record while still processing valid ones.

### Input: `transfers_invalid_batch.json`
11 transfer items (2 valid, 9 invalid):

```json
[
  {
    "date": "2026-02-23",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "amount": "100.00",
    "notes": "INVALID BATCH: Item 1 - Valid (for comparison)"
  },
  {
    "date": "2026-02-23",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "amount": "-50.00",
    "notes": "INVALID BATCH: Item 2 - Negative amount"
  },
  {
    "date": "2026-02-23",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "amount": "0.00",
    "notes": "INVALID BATCH: Item 3 - Zero amount"
  },
  {
    "date": "2026-02-23",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "amount": "75.00",
    "currency": "SGD",
    "currency_amount": "75.00",
    "notes": "INVALID BATCH: Item 4 - Over-specified (no exchange_rate)"
  },
  {
    "date": "2026-02-23",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "currency": "USD",
    "currency_amount": "60.00",
    "notes": "INVALID BATCH: Item 5 - Currency mismatch (USD not from_account)"
  },
  {
    "date": "2026-02-23",
    "from_account": "Nonexistent Account",
    "to_account": "TWH IB USD",
    "amount": "100.00",
    "notes": "INVALID BATCH: Item 6 - Nonexistent from_account"
  },
  {
    "date": "2026-02-23",
    "from_account": "TWH - Personal",
    "to_account": "Nonexistent Account",
    "amount": "100.00",
    "notes": "INVALID BATCH: Item 7 - Nonexistent to_account"
  },
  {
    "date": "2026-02-23",
    "from_account": "TWH - Personal",
    "to_account": "TWH - Personal",
    "amount": "100.00",
    "notes": "INVALID BATCH: Item 8 - Same from and to account"
  },
  {
    "date": "2026-02-23",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "notes": "INVALID BATCH: Item 9 NoAmount"
  },
  {
    "date": "2026-02-23",
    "from_account": "TWH - Personal",
    "to_account": "TWH IB USD",
    "currency": "EUR",
    "currency_amount": "70.00",
    "notes": "INVALID BATCH: Item 10 ThirdCurrency"
  },
  {
    "date": "2026-02-23",
    "from_account": "TWH IB USD",
    "to_account": "TWH - Personal",
    "amount": "250.00",
    "notes": "INVALID BATCH: Item 11 Valid"
  }
]
```

### Expected Command Output
```
Batch import completed
  Successful: 2
  Failed: 9

Failed records:
  2026-02-23 TWH - Personal -> TWH IB USD: Invalid amount (must be positive)
  2026-02-23 TWH - Personal -> TWH IB USD: Invalid amount (must be positive)
  2026-02-23 TWH - Personal -> TWH IB USD: Cannot specify both amount and currency_amount without exchange_rate
  2026-02-23 TWH - Personal -> TWH IB USD: Transfer currency must match from_account currency
  2026-02-23 Nonexistent Account -> TWH IB USD: Account not found: Nonexistent Account
  2026-02-23 TWH - Personal -> Nonexistent Account: Account not found: Nonexistent Account
  2026-02-23 TWH - Personal -> TWH - Personal: From and to accounts must be different
  2026-02-23 TWH - Personal -> TWH IB USD: Amount or currency_amount must be specified
  2026-02-23 TWH - Personal -> TWH IB USD: Currency must match from_account or to_account
```

### Expected Results

**Successful (2 created):**
- ✅ **Item 1:** SGD->USD, 100 (valid)
- ✅ **Item 11:** USD->SGD, 250 (valid)

**Failed (9 rejected):**
- ❌ **Item 2:** Negative amount (-50.00)
- ❌ **Item 3:** Zero amount (0.00)
- ❌ **Item 4:** Over-specified (amount + currency_amount, no rate)
- ❌ **Item 5:** Currency mismatch (USD doesn't match from_account SGD)
- ❌ **Item 6:** Nonexistent from_account
- ❌ **Item 7:** Nonexistent to_account
- ❌ **Item 8:** Same from and to account
- ❌ **Item 9:** Missing amount and currency_amount
- ❌ **Item 10:** 3rd currency (EUR doesn't match from_account SGD or to_account USD)

### Validation

- ✅ Only 2 transfers created in database
- ✅ Only 2 SyncUpdate records created
- ✅ Failed items produce clear, specific error messages
- ✅ Only 2 transfers visible in mobile app (Items 1 and 11)
- ✅ No mobile app data for any failed items
- ✅ Processing continued for all items despite errors (no early termination)

---

## Running the Tests

### Run Valid Batch Test
```bash
python tests/manual/manual_test_runner.py --test-id uat_batch_transfer_valid
```

### Run Invalid Batch Test
```bash
python tests/manual/manual_test_runner.py --test-id uat_batch_transfer_invalid
```

### View Available Batch Tests
```bash
python tests/manual/manual_test_runner.py --list | grep batch_transfer
```

---

## Batch Testing Benefits

1. **Efficiency:** Test 7+ scenarios in single batch instead of 7+ individual test runs
2. **Error Handling:** Validate error reporting and continue-on-error behavior
3. **Parsing Error Visibility:** Verify parsing errors are displayed (not silently dropped)
4. **Sync Validation:** Verify SyncUpdates are created correctly for batch operations
5. **Real-world Usage:** Users often import transfers from external systems (spreadsheets, other apps)
6. **Cross-scenario Coverage:** Mix of base→foreign, foreign→base, foreign→foreign, same-currency, inferred vs explicit in one test
7. **Specification Methods:** Tests both inference (amount only) and explicit specification (currency + currency_amount)

---

## Cleanup

**Both Tests Now Use Automated Rollback:**
- Test runner records transfer keys from batch output
- Automated rollback step uses `hb batch run` with `rollback_transfers.json` template
- Template expands `{TRANSFER_KEYS}` to individual delete operations

**Manual Cleanup (if needed):**
```bash
python tests/manual/find_and_delete_transfers.py --date 2026-02-22 --from-account "TWH - Personal" --to-account "TWH IB USD" --amount 200.00
```

---

## JSON Format Reference

**Required Fields:**
- `date` - YYYY-MM-DD format
- `from_account` - Account name (must exist)
- `to_account` - Account name (must exist)
- `amount` - Decimal value (for inference) OR explicitly specify`currency` + `currency_amount`

**Optional Fields:**
- `notes` - Transfer notes/description
- `currency` - Must match from_account currency (inferred if not specified)
- `currency_amount` - Amount in from_account currency (inferred if not specified)

**Validation Rules:**
- **Cannot specify both `amount` and `currency_amount` without `exchange_rate`** (ambiguous)
- `currency` must match `from_account` currency (if specified)
- `amount` and `currency_amount` must be positive (> 0)
- From and to accounts must be different
- From and to accounts must exist in database
