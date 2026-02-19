# Issue 001 Sync Detection Diagnostics Plan

## Table of contents

- [Goal](#goal)
- [Current observations](#current-observations)
- [Diagnostics](#diagnostics)
  - [Latest Findings](#latest-findings-2026-02-17)
  - [Phase 1: SyncUpdate Discovery](#phase-1-syncupdate-discovery)
  - [Phase 2: Payload Encoding Refinement](#phase-2-payload-encoding-refinement)
- [Diagnostic Steps](#diagnostic-steps)
- [Resolution](#resolution)

## Goal

Identify how sync detection works and why wrapper added expenses do not sync to mobile.

## Current observations

- Logs show repeated DNS failures for homebudgetsync.appspot.com in both snapshots.
- Prefs and version files appear unchanged across snapshots.

## Diagnostics

### Latest Findings (2026-02-17)

**Issue Status**: RESOLVED ✓

**Root Cause Identified**: Native app uses full zlib compression format with header (wbits=15), not raw deflate (wbits=-15)

**Key Discoveries**:
- Wrapper payloads were incorrectly using raw deflate after stripping the zlib header
- Native app compression: `zlib.compress()` directly with full format (level 9)
- Wrapper must pad compressed data to exactly 660 bytes with null bytes before base64 encoding
- URL-safe base64 encoding required (using `-` and `_` instead of `+` and `/`)
- Final payload format: 880 characters (660 bytes base64 encoded)

**Implementation Status**:
- ✓ Encoder corrected to use full zlib format (wbits=15)
- ✓ Decoder corrected to match encoder
- ✓ Mobile sync test PASSED — wrapper-generated expense synced to mobile device
- ✓ Both wrapper and native payloads decode successfully

### Phase 1: SyncUpdate Discovery

**Initial Problem**: Wrapper created expenses but they did not sync to mobile despite no obvious errors.

**Investigation Approach**:
- Compare non-database files first to find sync metadata outside SQLite
- Compare database snapshots with focus on sync-related tables and change tracking columns
- Map deltas to test expense to identify sync detection markers
- Form hypotheses from deltas, then validate with targeted queries

**Key Discovery**: SyncUpdate table is the sync queue mechanism

**Findings**:
- Prefs.json and version.plist showed no changes between before/after snapshots
- Logs showed repeated DNS failures (not relevant to local sync)
- Row counts unchanged for all tables **except SyncUpdate** (dropped by 3 rows)
- SyncInfo, DeviceInfo, and Settings rows were unchanged
- **SyncUpdate payloads decode to JSON operations** including AddExpense for test expense

**SyncUpdate Table Structure**:
- Primary key field: `key`
- Update type field: `updateType` (e.g., "AddExpense", "UpdateExpense")
- Payload field: `payload` (base64 encoded, zlib compressed JSON)
# Issue 001 Sync Detection Diagnostics

## Table of contents

- [Goal](#goal)
- [Current observations](#current-observations)
- [Investigation summary](#investigation-summary)
- [Phase 1 SyncUpdate discovery](#phase-1-syncupdate-discovery)
- [Phase 2 encoding validation](#phase-2-encoding-validation)
- [Phase 3 payload structure validation](#phase-3-payload-structure-validation)
- [Update operations and attribute fan out](#update-operations-and-attribute-fan-out)
- [Resolution](#resolution)
- [References](#references)

## Goal

Identify how sync detection works and why wrapper created expenses did not sync to mobile.

## Current observations

- Logs showed repeated DNS failures to the sync host in both snapshots
- Prefs and version files appeared unchanged across snapshots

## Investigation summary

The investigation confirmed that SyncUpdate is the sync queue, payload structure is operation specific, and encoding rules must match the native app. The wrapper initially failed in two areas:

- It did not create SyncUpdate entries
- It created payloads with incorrect encoding and structure

## Phase 1 SyncUpdate discovery

### Method

- Compare non database files to find external sync metadata
- Compare database snapshots for row count and field deltas
- Inspect SyncUpdate payloads for operation content

### Findings

- SyncUpdate was the only table with row count changes
- SyncInfo and DeviceInfo remained unchanged
- SyncUpdate payloads decoded to JSON operations including AddExpense
- Wrapper created Expense rows without SyncUpdate entries

### Conclusion

Sync detection is driven by SyncUpdate. The wrapper must insert SyncUpdate entries for each operation in the same transaction.

## Phase 2 encoding validation

### Hypotheses and tests

1. Base64 format mismatch
   - Wrapper used standard base64
   - Native app used URL safe base64
   - Result, URL safe base64 required

2. Payload length rules
   - Native app payloads varied in length, not fixed size
   - Small payloads were padded to a minimum byte length
   - Result, padding must follow operation specific rules

3. Compression format
   - Raw deflate failed for native payloads
   - Full zlib format with header and checksum worked
   - Result, wbits 15 required

### Correct encoding flow

1. Serialize operation to compact JSON
2. Compress with full zlib format using wbits 15 and compression level 9
3. If configured, pad to a minimum size with null bytes
4. Encode with URL safe base64
5. Strip trailing = padding

### Outcome

Wrapper payloads decoded successfully and were accepted by the sync service after applying these rules.

## Phase 3 payload structure validation

### Key structure findings

- Expense Add uses an array key field named expenseDeviceKeys
- Expense Update and Delete use a singular key field named expenseDeviceKey
- Income uses a singular key field named deviceKey for all operations
- Delete operations use minimal payloads and do not include full transaction fields

### Structural differences that caused failures

- DeleteExpense payloads must contain only Operation, expenseDeviceKey, and deviceId
- Using expenseDeviceKeys in DeleteExpense caused rejection
- Including full expense fields in DeleteExpense caused rejection

### Configuration driven mapping

The wrapper now reads [src/python/homebudget/sync-config.json](../../src/python/homebudget/sync-config.json) to define field lists, key formats, and compression rules per operation. This removed hard coded payload logic and makes operation differences explicit.

## Update operations and attribute fan out

The native app emits one sync event per changed attribute during updates. The wrapper matches this behavior by creating multiple SyncUpdate entries for a single update call, one per changed field, using the final record state in each payload.

This behavior is implemented in `create_updates_for_changes` in [src/python/homebudget/sync.py](../../src/python/homebudget/sync.py).

## Resolution

### Implementation summary

- Added SyncUpdate creation for all operations
- Implemented config driven payload creation per resource and operation
- Fixed encoding to use full zlib format and URL safe base64
- Added operation specific padding rules with a minimum byte size
- Implemented update attribute fan out to create one entry per changed field

### Validation

- Wrapper payloads decode successfully using the decoder in [tests/manual/verify_syncupdate.py](../../tests/manual/verify_syncupdate.py)
- Mobile sync succeeds for Add, Update, and Delete expense operations

## References

- [Issue 001 Sync Detection](001-sync-detection.md)
- [Sync Update Mechanism](../sync-update.md)
- List row counts for all tables in both databases.

- Identify tables with row count changes beyond Expense and AccountTrans.


