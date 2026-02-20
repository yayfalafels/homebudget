# Manual test result

## Table of contents

- [Summary](#summary)
- [Step results](#step-results)

## Summary

Test id: uat_batch_mixed_operations
Title: UAT: Mixed batch operations across resources
Timestamp: 2026-02-20T13:10:25
Overall result: pass
Overall notes: 

## Step results

### Step 1
Kind: user
Label: Confirm hb-config.json is configured and connected to WiFi
Command: none
Status: pass
Notes: 

### Step 2
Kind: auto
Label: Build batch step 1 file for single expense add
Command: python tests/manual/build_batch_operations.py --mode step1 --output tests/manual/results/batch_step1.json
Status: pass
Notes: 

### Step 3
Kind: auto
Label: Run batch step 1
Command: hb sync batch --file tests/manual/results/batch_step1.json
Status: pass
Notes: 

### Step 4
Kind: user
Label: Verify batch step 1 completed successfully in both apps
Command: none
Status: pass
Notes: 

### Step 5
Kind: auto
Label: List expenses to get key
Command: hb expense list --start-date 2026-02-20 --end-date 2026-02-20 --account "TWH - Personal" --limit 5
Status: pass
Notes: 

### Step 6
Kind: user
Label: Record the expense key
Command: none
Status: pass
Notes: Recorded: expense_key = 13141

### Step 7
Kind: auto
Label: Build batch step 2 file for expense update
Command: python tests/manual/build_batch_operations.py --mode step2 --expense-key 13141 --output tests/manual/results/batch_step2.json
Status: pass
Notes: 

### Step 8
Kind: auto
Label: Run batch step 2
Command: hb sync batch --file tests/manual/results/batch_step2.json
Status: pass
Notes: 

### Step 9
Kind: user
Label: Verify batch step 2 (expense update) completed successfully in both apps
Command: none
Status: pass
Notes: 

### Step 10
Kind: auto
Label: Build batch step 3 file for expense delete and add income and transfer
Command: python tests/manual/build_batch_operations.py --mode step3 --expense-key 13141 --output tests/manual/results/batch_step3.json
Status: pass
Notes: 

### Step 11
Kind: auto
Label: Run batch step 3
Command: hb sync batch --file tests/manual/results/batch_step3.json
Status: pass
Notes: 

### Step 12
Kind: user
Label: Verify batch step 3 (delete expense, add income, add transfer) completed successfully in both apps
Command: none
Status: pass
Notes: 

### Step 13
Kind: auto
Label: List incomes to get key
Command: hb income list --start-date 2026-02-20 --end-date 2026-02-20 --limit 5
Status: pass
Notes: 

### Step 14
Kind: user
Label: Record the income key
Command: none
Status: pass
Notes: Recorded: income_key = 1497

### Step 15
Kind: auto
Label: List transfers to get key
Command: hb transfer list --start-date 2026-02-20 --end-date 2026-02-20 --limit 5
Status: pass
Notes: 

### Step 16
Kind: user
Label: Record the transfer key
Command: none
Status: pass
Notes: Recorded: transfer_key = 11724

### Step 17
Kind: auto
Label: Build rollback batch file for income and transfer
Command: python tests/manual/build_batch_operations.py --mode rollback --income-key 1497 --transfer-key 11724 --output tests/manual/results/batch_rollback.json
Status: pass
Notes: 

### Step 18
Kind: auto
Label: Run rollback batch
Command: hb sync batch --file tests/manual/results/batch_rollback.json
Status: pass
Notes: 

### Step 19
Kind: user
Label: Verify batch operations completed and test data is removed
Command: none
Status: pass
Notes: 

