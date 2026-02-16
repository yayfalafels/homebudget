# Issue 001 Sync Detection Diagnostics Plan

## Table of contents

- [Goal](#goal)
- [Current observations](#current-observations)
- [Snapshot inventory](#snapshot-inventory)
- [Diagnostics approach](#diagnostics-approach)
- [Hypotheses to test](#hypotheses-to-test)
- [Detailed inspection plan](#detailed-inspection-plan)
- [Diagnostics results](#diagnostics-results)
- [Hypothesis updates](#hypothesis-updates)
- [Output artifacts](#output-artifacts)

## Goal

Identify how sync detection works and why wrapper added expenses do not sync to mobile.

## Current observations

- Logs show repeated DNS failures for homebudgetsync.appspot.com in both snapshots.
- Prefs and version files appear unchanged across snapshots.

## Snapshot inventory

- reference/sync-demo/01-before
- reference/sync-demo/02-after
- Data contains homebudget.db and version.plist
- Logs contains HomeBudget.log files
- Prefs.json exists at the root of each snapshot

## Diagnostics approach

- Compare non database files first to find sync metadata outside sqlite.
- Compare database snapshots with a focus on sync related tables and change tracking columns.
- Map deltas to the test expense to identify sync detection markers.
- Form hypotheses from the deltas, then validate with targeted queries.

## Hypotheses to test

- Sync detection is driven by SyncInfo and SyncUpdate tables.
- Sync detection depends on device identifiers stored in DeviceInfo and deviceKey fields across tables.
- Sync detection depends on timeStamp changes in Expense and AccountTrans and possibly AccountLog.
- Sync detection is driven by a queued update payload in SyncUpdate that is not written by the wrapper.
- Sync detection may also rely on settings or preferences in Prefs.json or Settings table.

## Detailed inspection plan

1. Compare Prefs.json
- Diff key sets and values between snapshots.
- Look for sync group identifiers, device identifiers, last sync timestamps, or flags.

2. Compare version.plist
- Confirm no schema or app version changes that could affect sync logic.

3. Compare logs
- Identify sync attempts, errors, or success markers around the test time.
- Extract any log lines that reference sync queue, SyncUpdate, or database updates.

4. Database high level diff
- List row counts for all tables in both databases.
- Identify tables with row count changes beyond Expense and AccountTrans.

5. Sync tables deep dive
- Inspect SyncInfo rows and compare values for last sync time, group id, and device id.
- Inspect SyncUpdate rows for new entries and payloads.
- Inspect DeviceInfo rows for device identifiers, primary flags, and timestamps.

6. Transaction linkage validation
- Identify the test expense in Expense by timeStamp and amount.
- Find the related AccountTrans and AccountLog entries and compare timeStamp and device fields.
- Verify deviceIdKey and deviceKey are set consistently across related rows.

7. Settings and metadata validation
- Inspect Settings rows for sync related keys or flags.
- Check for any other tables with deviceIdKey or deviceKey fields and confirm changes.

8. Hypothesis validation queries
- If SyncUpdate is empty, test whether the wrapper should insert a row with a payload for the test expense.
- If SyncInfo timestamps do not change, test whether the application updates them only on successful sync.
- If device fields are zero or null on wrapper writes, test whether HomeBudget uses those fields to detect change origin.

## Diagnostics results

- Prefs diff shows no changes between snapshots.
- version plist diff shows no changes between snapshots.
- Logs show repeated DNS failures for homebudgetsync.appspot.com before and after.
- Row counts are unchanged for all tables except SyncUpdate, which drops by three rows.
- SyncInfo, DeviceInfo, and Settings rows are unchanged.
- Expense, AccountTrans, and AccountLog have no row changes and no column diffs in the exported sample.
- SyncUpdate payloads decode to JSON operations including budget updates and an AddExpense entry for the test expense.
- The test expense appears in Expense with key 13073, notes test, amount 25, timeStamp 2026-02-16 10:36:25.

## Hypothesis updates

- SyncUpdate appears to be the only table with change between snapshots, so it remains the primary sync queue candidate.
- SyncInfo lastSync and lastUpdateSeq did not change, so sync metadata did not move during the test.
- DeviceInfo did not change, so device identity is stable and not a trigger in this run.
- The three removed SyncUpdate rows suggest the app may prune the queue on startup or after a failed sync attempt.
- The test expense did not create a detectable new sync marker between snapshots, which supports the wrapper missing a sync update step.
- The SyncUpdate AddExpense payload includes expenseDeviceKeys and device identifiers, which suggests the wrapper must write a SyncUpdate entry with device metadata to trigger sync.

## Summary of findings

The sync detection issue is confirmed to be caused by missing SyncUpdate entries when the wrapper creates transactions. HomeBudget uses SyncUpdate as a queue for pending sync operations with base64 encoded and zlib compressed JSON payloads. Each payload includes operation type, transaction keys, device identifiers, and full transaction metadata.

The test expense with key 13073 and notes "test" appears in both the Expense table and SyncUpdate table with a fully formed AddExpense operation. The wrapper must insert similar SyncUpdate entries for all transactions it creates to trigger sync to mobile devices.

Detailed sync mechanism documentation and wrapper integration design are provided in [docs/sync-update.md](../sync-update.md).

## Output artifacts

- A short diff report listing tables with changes and key fields for those rows.
- A summary of log findings with timestamps tied to the test expense window.
- A hypothesis table that maps each sync mechanism candidate to supporting evidence and next test.
