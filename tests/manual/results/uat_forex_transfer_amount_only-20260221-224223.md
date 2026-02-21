# Manual test result

## Table of contents

- [Summary](#summary)
- [Step results](#step-results)

## Summary

Test id: uat_forex_transfer_amount_only
Title: UAT: Forex transfer amount only with inferred rate
Timestamp: 2026-02-21T22:44:25
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
Label: Create transfer from base to USD account with amount only
Command: hb transfer add --date 2026-02-20 --from-account "TWH - Personal" --to-account "TWH IB USD" --amount 100.00 --notes "UAT Forex Transfer Amount Only"
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
Label: Verify: Transfer appears in Windows and mobile apps with currency USD and calculated currency amount
Command: none
Status: pass
Notes: 

### Step 6
Kind: auto
Label: List transfers to get key
Command: hb transfer list --start-date 2026-02-20 --end-date 2026-02-20 --limit 5
Status: pass
Notes: 

### Step 7
Kind: user
Label: Record the forex transfer key
Command: none
Status: pass
Notes: Recorded: transfer_key = 11733

### Step 8
Kind: auto
Label: Read forex transfer
Command: hb transfer get 11733
Status: pass
Notes: 

### Step 9
Kind: user
Label: Verify: Currency fields are present and currency amount is calculated
Command: none
Status: pass
Notes: 

### Step 10
Kind: auto
Label: Delete forex transfer
Command: hb transfer delete 11733 --yes
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
Label: Verify: Forex transfer removed from Windows app and mobile app
Command: none
Status: pass
Notes: 

