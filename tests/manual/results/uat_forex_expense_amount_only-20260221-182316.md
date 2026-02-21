# Manual test result

## Table of contents

- [Summary](#summary)
- [Step results](#step-results)

## Summary

Test id: uat_forex_expense_amount_only
Title: UAT: Forex expense amount only with inferred rate
Timestamp: 2026-02-21T18:26:05
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
Kind: user
Label: Ensure mobile app is on WiFi and synced
Command: none
Status: pass
Notes: 

### Step 3
Kind: auto
Label: Create expense on USD account with amount only
Command: hb expense add --date 2026-02-20 --category "Food (Basic)" --subcategory "Cheap restaurant" --amount 25.50 --account "TWH IB USD" --notes "UAT Forex Expense Amount Only"
Status: pass
Notes: 

### Step 4
Kind: auto
Label: Verify SyncUpdate created
Command: python tests/manual/verify_syncupdate.py
Status: pass
Notes: 

### Step 5
Kind: user
Label: Verify: Expense appears in Windows and mobile apps with currency USD, currency amount 25.50, and converted base amount
Command: none
Status: pass
Notes: 

### Step 6
Kind: auto
Label: List expenses to get key
Command: hb expense list --start-date 2026-02-20 --end-date 2026-02-20 --account "TWH IB USD" --limit 5
Status: pass
Notes: 

### Step 7
Kind: user
Label: Record the forex expense key
Command: none
Status: pass
Notes: Recorded: expense_key = 13157

### Step 8
Kind: auto
Label: Read forex expense
Command: hb expense get 13157
Status: pass
Notes: 

### Step 9
Kind: user
Label: Verify: Currency fields are present and amount reflects conversion
Command: none
Status: pass
Notes: 

### Step 10
Kind: auto
Label: Delete forex expense
Command: hb expense delete 13157 --yes
Status: pass
Notes: 

### Step 11
Kind: auto
Label: Verify SyncUpdate created for delete
Command: python tests/manual/verify_syncupdate.py
Status: pass
Notes: 

### Step 12
Kind: user
Label: Verify: Forex expense removed from Windows app and mobile app
Command: none
Status: pass
Notes: 

