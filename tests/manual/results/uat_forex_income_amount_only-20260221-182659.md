# Manual test result

## Table of contents

- [Summary](#summary)
- [Step results](#step-results)

## Summary

Test id: uat_forex_income_amount_only
Title: UAT: Forex income amount only with inferred rate
Timestamp: 2026-02-21T18:36:14
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
Label: Create income on USD account with amount only
Command: hb income add --date 2026-02-20 --name "Salary and Wages" --amount 1000.00 --account "TWH IB USD" --notes "UAT Forex Income Amount Only"
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
Label: Verify: Income appears in Windows and mobile apps with currency USD, currency amount 1000.00, and converted base amount
Command: none
Status: pass
Notes: 

### Step 6
Kind: auto
Label: List incomes to get key
Command: hb income list --start-date 2026-02-20 --end-date 2026-02-20 --limit 5
Status: pass
Notes: 

### Step 7
Kind: user
Label: Record the forex income key
Command: none
Status: pass
Notes: Recorded: income_key = 1497

### Step 8
Kind: auto
Label: Read forex income
Command: hb income get 1497
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
Label: Delete forex income
Command: hb income delete 1497 --yes
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
Label: Verify: Forex income removed from Windows app and mobile app
Command: none
Status: pass
Notes: 

