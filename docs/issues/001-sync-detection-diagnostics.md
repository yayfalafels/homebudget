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
- UUID field: `uuid` (operation identifier)
- Timestamp tracking: `createdAt`, `updatedAt`

**Payload Content** (decoded JSON structure):
```json
{
  "op": "AddExpense",
  "key": 13073,
  "expenseDeviceKeys": [...],
  "deviceId": "...",
  "accountDeviceId": "...",
  "categoryDeviceId": "...",
  "amount": 25.00,
  "notes": "test",
  "category": "Food",
  "date": "2026-02-16"
}
```

**Initial Hypothesis Validation**:
- ✓ SyncUpdate is the sync queue (confirmed by presence of operation entries)
- ✓ Device identifiers are critical (present in all payloads with device metadata)
- ✓ Timestamps NOT the trigger (SyncInfo lastSync unchanged, SyncUpdate is queue)
- ✓ Payloads contain complete operation data (not metadata-only)

**Critical Insight**: The wrapper was **not creating any SyncUpdate entries**, while HomeBudget does create them on every transaction. This is why mobile sync never triggered.

### Phase 2: Payload Encoding Refinement

**Problem After Phase 1 Fix**: After implementing SyncUpdate entry creation, transactions still did not sync to mobile despite:
- SyncUpdate entries created successfully
- Entries consumed by sync service when WiFi connects
- Wrapper payloads decoded correctly

**Root Cause Investigation**: Payload encoding format mismatch between wrapper and native app

**Discoveries Through Systematic Testing**:

| Aspect | Wrapper (Initial) | Native App | Issue |
|--------|-------------------|------------|-------|
| Compression | Raw deflate (wbits=-15) | Full zlib (wbits=15) | ❌ Mismatch |
| Padding | Variable length | 660 bytes always | ❌ Length mismatch |
| Base64 | Standard (`+`, `/`) | URL-safe (`-`, `_`) | ❌ Character mismatch |
| Result length | 418 characters | 880 characters | ❌ Sync rejection likely |

**Theory 1: Base64 Encoding Format**
- Hypothesis: Wrapper uses standard, native uses URL-safe
- Finding: URL-safe is presentation difference only
- Result: Ruled out as primary cause, but necessary to fix

**Theory 2: Payload Length (CONFIRMED)**
- Hypothesis: Sync service requires fixed 880-character size
- Finding: Native app pads compressed data to exactly 660 bytes (→ 880 chars in base64)
- Result: **This is likely the sync rejection cause**
- Validation: Base64 decode 880-char → 660 bytes, contains null byte padding

**Theory 3: Compression Algorithm**
- Hypothesis: Different zlib compression settings
- Finding: Both use level 9, but wrapper incorrectly strips zlib header
- Result: Ruled out, but header stripping is the deeper problem

**Theory 4: Compression Format (BREAKTHROUGH)**
- Hypothesis: Wrapper uses raw deflate, native uses something else
- Testing: Systematically tested all zlib decompression modes (wbits values)
  - Raw deflate (wbits=-15): Failed — "invalid stored block lengths"
  - Raw deflate (wbits=-zlib.MAX_WBITS): Failed — "invalid stored block lengths"
  - **Full zlib format (wbits=15): SUCCESS** ✓
- Finding: Native app uses `zlib.compress()` directly (full format with header + checksum)
- Result: **Root cause identified** — Wrapper incorrectly assumes raw deflate

**Correct Encoding Sequence** (discovered through Phase 2):
1. JSON serialize operation data
2. Compress with full zlib: `zlib.compress(json_bytes, level=9)` (NOT raw deflate)
3. Pad compressed data to 660 bytes with null bytes (0x00)
4. Encode with URL-safe base64: `base64.urlsafe_b64encode(padded)`
5. Strip trailing `=` padding from base64 string
6. Result: 880-character payload string

## Diagnostic Steps

### Phase 1: Investigation Methodology

The following steps were used to discover SyncUpdate and understand the sync mechanism:

- reference/sync-demo/01-before
- reference/sync-demo/02-after
- Data contains homebudget.db and version.plist
- Logs contains HomeBudget.log files
- Prefs.json exists at the root of each snapshot

### Hypotheses to Test (Phase 1)

- Sync detection is driven by SyncInfo and SyncUpdate tables.
- Sync detection depends on device identifiers stored in DeviceInfo and deviceKey fields across tables.
- Sync detection depends on timeStamp changes in Expense and AccountTrans and possibly AccountLog.
- Sync detection is driven by a queued update payload in SyncUpdate that is not written by the wrapper.
- Sync detection may also rely on settings or preferences in Prefs.json or Settings table.

### Payload Encoding Testing Approach (Phase 2)

### Payload Encoding Testing Approach (Phase 2)

After discovering SyncUpdate, the wrapper created entries but mobile sync still failed. Phase 2 used systematic comparison to identify encoding differences:

1. **Payload Size Measurement** — Compare character counts and byte sizes
2. **Base64 Analysis** — Identify character set differences (standard vs URL-safe)
3. **Decompression Testing** — Try all zlib modes (wbits values) against native payloads
4. **Compression Validation** — Confirm padding strategy and bytes before compression
5. **Round-trip Verification** — Encode test data, decode, verify structure matches

### Detailed Inspection Plan (Phase 1)

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

### Diagnostics Results

- Prefs diff shows no changes between snapshots.
- version plist diff shows no changes between snapshots.
- Logs show repeated DNS failures for homebudgetsync.appspot.com before and after.
- Row counts are unchanged for all tables except SyncUpdate, which drops by three rows.
- SyncInfo, DeviceInfo, and Settings rows are unchanged.
- Expense, AccountTrans, and AccountLog have no row changes and no column diffs in the exported sample.
- SyncUpdate payloads decode to JSON operations including budget updates and an AddExpense entry for the test expense.
- The test expense appears in Expense with key 13073, notes test, amount 25, timeStamp 2026-02-16 10:36:25.

### Phase 1 Results: SyncUpdate Discovery

**Hypothesis Updates**:
- ✓ SyncUpdate is the only table with changes (primary sync queue candidate confirmed)
- ✓ SyncInfo lastSync and lastUpdateSeq unchanged (sync metadata not updated yet)
- ✓ DeviceInfo unchanged (device identity stable, not a trigger)
- ✓ Three removed SyncUpdate rows suggest app prunes queue on startup or after failed sync
- ✓ Test expense appears in Expense table but had no SyncUpdate entry initially
- ✓ **Root cause of Phase 1**: Wrapper was not creating SyncUpdate entries at all

**Critical Finding**: HomeBudget creates SyncUpdate entries for every transaction. The wrapper must replicate this behavior.

### Phase 2 Results: Payload Encoding Validation

**Systematic Testing Outcomes**:
- Raw deflate decompression: FAILED ("invalid stored block lengths")
- Full zlib format decompression: SUCCESS (wbits=15)
- URL-safe base64: Required (native app uses `-` and `_`)
- Fixed payload length: Required (880 characters = 660 bytes binary)

**Critical Finding**: Native app uses `zlib.compress()` directly (full format), not raw deflate. Wrapper was incorrectly stripping header and checksum bytes.

### Summary of Complete Investigation

**Phase 1** identified that SyncUpdate is the sync mechanism and that the wrapper was not creating entries.

**Phase 2** identified that even after creating entries, they were rejected because of encoding mismatches in compression format, padding, and base64 variant.

**Full Solution**:
1. Create SyncUpdate entries for every transaction (Phase 1)
2. Use correct encoding: full zlib + 660-byte padding + URL-safe base64 (Phase 2)

Detailed sync mechanism documentation and wrapper integration design are provided in [docs/sync-update.md](../sync-update.md).

## Resolution

### Implementation Status (2026-02-17)

**RESOLVED**: Mobile sync test PASSED ✓

**Files Modified**:
- `src/python/homebudget/sync.py` — Updated encoder to use full zlib format with 660-byte padding
- `tests/manual/verify_syncupdate.py` — Updated decoder to use wbits=15 for full zlib format

**Key Changes**:
1. Removed incorrect header/checksum stripping from encoder
2. Changed to URL-safe base64 encoding (`base64.urlsafe_b64encode`)
3. Ensured all payloads are exactly 880 characters (660 bytes binary)
4. Updated decoder to use `wbits=15` instead of `wbits=-15`

**Validation**:
- Wrapper payload: 880 characters, decodes successfully
- Native payload: 880 characters, decodes successfully
- Mobile device: Expense appears within 30 seconds of sync

### Followup Investigation: Payload Encoding Issues

#### Date

2026-02-17

#### Problem

After implementing SyncUpdate entry creation in the wrapper, transactions still do not sync to mobile devices although:
- SyncUpdate entries are created successfully
- Entries are consumed by the sync service when WiFi connects
- Wrapper-generated payloads decode correctly

#### Investigation Process

##### Theory 1: Payload Encoding Format

**Hypothesis**: Wrapper payloads use different base64 encoding than native app

**Test**: Compare base64 characteristics of wrapper vs native payloads
- Wrapper payload: 418 characters, standard base64
- Native payload: 880 characters, contains `-` and `_` characters
- Result: Native app uses URL-safe base64 encoding

**Outcome**: Ruled out as primary cause. URL-safe base64 is a presentation difference, not functional.

##### Theory 2: Payload Length Affects Sync Acceptance

**Hypothesis**: Sync service rejects variable-length payloads

**Test**: Compare payload lengths in SyncUpdate table
```sql
SELECT key, updateType, uuid, length(payload) as plen 
FROM SyncUpdate ORDER BY key DESC LIMIT 5
```
- Wrapper payloads: 418 bytes
- Native app payloads: 880 bytes (consistent)
- Result: Native app pads all payloads to fixed 880-byte length

**Validation technique**: 
1. Base64 decode 880-char string → 660 bytes binary
2. Native app pads compressed zlib data to 660 bytes with null bytes (0x00)
3. These null bytes encode as 'A' characters in base64

**Outcome**: **CONFIRMED** - This is likely the sync rejection cause.

##### Theory 3: Payload Structure Differences

**Hypothesis**: Wrapper payloads missing required fields

**Test**: Decode and compare JSON structure
- Wrapper payload fields match native app exactly
- deviceId, accountDeviceId, categoryDeviceId all present
- Device identifiers match database DeviceInfo records
- Result: No structural differences

**Outcome**: Ruled out. Payload content is correct.

##### Theory 4: Compression Algorithm Differences

**Hypothesis**: Wrapper uses different zlib compression settings

**Test**: Examine compression approach
- Native app: zlib level 9, raw deflate (no header/checksum)
- Wrapper: zlib level 9, raw deflate (strips 2-byte header, 4-byte checksum)
- Result: Compression approach matches

**Outcome**: Ruled out. Compression is identical.

#### Decoder Validation Logic

Valid HomeBudget SyncUpdate payload structure:
1. 880 characters of URL-safe base64 (using `-` for `+`, `_` for `/`)
2. Base64 decodes to 660 bytes of binary data
3. Binary data = raw zlib deflate stream + null byte padding to 660 bytes
4. Strip trailing 0x00 bytes from binary
5. Decompress using `zlib.decompress(data, wbits=-zlib.MAX_WBITS)` for raw deflate
6. Result is UTF-8 encoded JSON

Correct decoding sequence:
```python
def decode_sync_payload(payload: str) -> dict:
    # Step 1: Convert URL-safe base64 to standard
    cleaned = payload.strip().replace('-', '+').replace('_', '/')
    
    # Step 2: Add padding if needed
    if len(cleaned) % 4 != 0:
        padding = '=' * (-len(cleaned) % 4)
        cleaned = cleaned + padding
    
    # Step 3: Base64 decode to binary
    raw = base64.b64decode(cleaned)
    
    # Step 4: Strip trailing null bytes
    raw = raw.rstrip(b'\x00')
    
    # Step 5: Decompress raw deflate
    inflated = zlib.decompress(raw, wbits=-zlib.MAX_WBITS)
    
    # Step 6: Parse JSON
    return json.loads(inflated.decode('utf-8'))
```

#### Decoder Troubleshooting Attempts

**Attempt 1**: Strip trailing 'A' from base64 string before decode
- Failed: Legitimate compressed data can end with bytes that encode to 'A'

**Attempt 2**: Use standard base64 without URL-safe conversion
- Failed: Native app uses `-` and `_`, standard decoder rejects these

**Attempt 3**: Progressively strip 'A' characters and retry decode
- Failed: Too aggressive, removes valid data

**Attempt 4**: Decode full 880 chars, strip null bytes from binary
- **Current approach**: Works for wrapper payloads
- **Native payloads**: Still failing with "invalid stored block lengths" zlib error

#### Current Status

**Working**:
- Wrapper payload encoding (now pads to 660 bytes → 880 base64 chars)
- Wrapper payload decoding
- SyncUpdate entry creation with correct device identifiers

**Not working**:
- Native app payload decoding (zlib decompression fails)
- Sync to mobile (likely due to incorrect payload length in earlier tests)

#### Native Payload Decoding Analysis

**RESOLVED** (2026-02-17 14:11)

**Discovery**: Native app uses **full zlib compression format with header**, not raw deflate

**Testing process**:
Systematically tested all zlib decompression approaches using script `.dev/.scripts/test_all_zlib_approaches.py`:
- Raw deflate (wbits=-15): FAILED - "invalid stored block lengths"
- Raw deflate (wbits=-zlib.MAX_WBITS): FAILED - "invalid stored block lengths"
- **Full zlib format (wbits=15): SUCCESS** ✓
- Zlib format (default wbits): SUCCESS ✓
- Gzip format (wbits=16+15): Not tested (unnecessary)

**Key finding**: The correct decompression uses `zlib.decompress(raw, wbits=15)` which handles the full zlib format including header and checksum.

**Initial assumption error**: Wrapper incorrectly assumed native app used raw deflate and stripped the zlib header/checksum bytes. The native app actually uses `zlib.compress()` directly without modification.

**Correct encoding sequence**:
1. JSON serialize operation data
2. Compress with full zlib: `zlib.compress(json_bytes, level=9)`
3. Pad compressed data to 660 bytes with null bytes
4. Encode with URL-safe base64: `base64.urlsafe_b64encode(padded)`
5. Strip trailing '=' padding from base64 string
6. Result: 880-character payload string

**Validation**: Both wrapper-generated and native app payloads decode successfully using the corrected decoder with `wbits=15`.

#### Resolution Summary

**Implementation corrected** (2026-02-17):

1. ✓ Updated `src/python/homebudget/sync.py` to use full zlib format
2. ✓ Changed to URL-safe base64 encoding
3. ✓ Maintained 660-byte padding for 880-character output
4. ✓ Updated `tests/manual/verify_syncupdate.py` decoder to use wbits=15
5. ✓ Tested wrapper payload: 880 characters, decodes successfully
6. ✓ Tested native payload: 880 characters, decodes successfully
7. ✓ **Mobile sync test: PASSED** - Wrapper-generated expense synced to mobile device

**Files modified**:
- `src/python/homebudget/sync.py`: Removed header stripping, added URL-safe encoding
- `tests/manual/verify_syncupdate.py`: Changed wbits from -15 to 15

#### Test Plan for Wrapper Payload Validation

1. Reinstall wrapper with padding fix: `pip install -e .`
2. Clear existing SyncUpdate table: `DELETE FROM SyncUpdate`
3. Add test expense via wrapper CLI
4. Verify SyncUpdate entry is 880 bytes: `SELECT length(payload) FROM SyncUpdate ORDER BY key DESC LIMIT 1`
5. Decode wrapper payload to confirm structure: `python tests/manual/verify_syncupdate.py --print-payload`
6. Connect to WiFi
7. Verify entry consumed from SyncUpdate table
8. **Critical test**: Check if expense appears on mobile device
9. If mobile sync works: **Issue resolved**
10. If mobile sync fails: Investigate sync service logs, device registration, or other requirements

#### Final Implementation

**File**: `src/python/homebudget/sync.py`
```python
def encode_payload(self, operation: dict) -> str:
    json_str = json.dumps(operation, separators=(",", ":"))
    # Use full zlib compression with header (matches native app)
    compressed = zlib.compress(json_str.encode("utf-8"), level=9)
    
    # Pad to 660 bytes to match native app fixed-size format
    target_raw_length = 660
    if len(compressed) < target_raw_length:
        compressed = compressed + b'\x00' * (target_raw_length - len(compressed))
    
    # Use URL-safe base64 encoding (matches native app)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
    return encoded.rstrip("=")  # Strip padding
```

**File**: `tests/manual/verify_syncupdate.py`
```python
def _decode_sync_payload(payload: str) -> dict[str, Any]:
    cleaned = payload.strip()
    
    # HomeBudget uses URL-safe base64
    cleaned = cleaned.replace('-', '+').replace('_', '/')
    
    # Add padding if needed
    if len(cleaned) % 4 != 0:
        padding = '=' * (-len(cleaned) % 4)
        cleaned = cleaned + padding
    
    # Decode base64
    raw = base64.b64decode(cleaned)
    
    # Strip trailing null bytes (660-byte padding)
    raw = raw.rstrip(b'\x00')
    
    # Decompress using full zlib format (wbits=15)
    inflated = zlib.decompress(raw, wbits=15)
    
    # Parse JSON
    return json.loads(inflated.decode('utf-8'))
```

#### Key Insights

1. **Compression format discovery**: The native app uses full zlib format with header and checksum, not raw deflate. This was discovered by systematically testing all zlib decompression modes (wbits values).

2. **Encoding complete**: The wrapper successfully generates 880-character payloads matching native app format:
   - Full zlib compression (no header stripping)
   - 660-byte padding with null bytes
   - URL-safe base64 encoding
   - Produces consistent 880-character strings

3. **Decoding complete**: Both wrapper and native payloads decode successfully using `wbits=15` for full zlib format.

4. **Sync validation**: Mobile sync test confirmed working - wrapper-generated expense appeared on mobile device.

5. **Analysis approach**: Initial attempts failed because they assumed raw deflate format. The breakthrough came from testing all possible zlib decompression modes systematically rather than making assumptions about the format.


