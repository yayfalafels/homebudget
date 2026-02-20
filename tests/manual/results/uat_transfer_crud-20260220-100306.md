# Manual test result

## Table of contents

- [Summary](#summary)
- [Step results](#step-results)

## Summary

Test id: uat_transfer_crud
Title: UAT: Transfer CRUD with sync validation
Timestamp: 2026-02-20T10:05:01
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
Label: Record transfer count from both Windows and mobile apps, ensure mobile is on WiFi
Command: none
Status: pass
Notes: 

### Step 3
Kind: auto
Label: Create test transfer
Command: hb transfer add --date 2026-02-17 --from-account "TWH - Personal" --to-account "30 CC Hashemis" --amount 100.00 --notes "UAT Transfer Create 01"
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
Label: Verify: New transfer appears in Windows app AND mobile app
Command: none
Status: pass
Notes: 

### Step 6
Kind: auto
Label: List transfers to get key
Command: hb transfer list --start-date 2026-02-17 --end-date 2026-02-17 --limit 20
Status: pass
Notes: 

### Step 7
Kind: user
Label: Record the transfer key
Command: none
Status: pass
Notes: Recorded: transfer_key = 11724

### Step 8
Kind: auto
Label: Read transfer
Command: hb transfer get 11724
Status: pass
Notes: 

### Step 9
Kind: user
Label: Verify: Transfer details match what was entered
Command: none
Status: pass
Notes: 

### Step 10
Kind: auto
Label: Update transfer
Command: hb transfer update 11724 --amount 150.00 --notes "UAT Transfer Updated 01"
Status: pass
Notes: 

### Step 11
Kind: auto
Label: Verify SyncUpdate created for update
Command: python tests/manual/verify_syncupdate.py
Status: pass
Notes: 

### Step 12
Kind: user
Label: Verify: Updated transfer appears in Windows app AND mobile app
Command: none
Status: pass
Notes: 

### Step 13
Kind: auto
Label: Delete transfer
Command: hb transfer delete 11724 --yes
Status: pass
Notes: 

### Step 14
Kind: auto
Label: Verify SyncUpdate created for delete
Command: python tests/manual/verify_syncupdate.py
Status: pass
Notes: 

### Step 15
Kind: user
Label: Verify: Transfer removed from Windows app AND mobile app
Command: none
Status: pass
Notes: 

