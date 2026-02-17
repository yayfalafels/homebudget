# Issue 002: Delete Operation Sync Failure

## Status: RESOLVED (2026-02-17)

**Issue Description**: Delete SyncUpdate entries were created but not syncing to mobile app.

**Root Cause**: Delete operations require a **completely different payload structure** than Add/Update operations. The wrapper was incorrectly using the same full expense payload for all operations.

**Fix Applied**: Modified SyncUpdateManager to generate operation-specific payloads.

---

## Root Cause Analysis

### Discovery Process

Using the diagnostic approach from Issue 001, inspection of actual SyncUpdate payloads revealed:

**Add/Update Payload Structure** (20+ fields):
```json
{
  "Operation": "AddExpense|UpdateExpense",
  "expenseDeviceKeys": [13120],           // ARRAY
  "amount": 25.50,
  "currencyAmount": "25.50",
  "periods": 1,
  "accountDeviceKey": 2,
  "categoryDeviceKey": 5,
  "subcategoryDeviceKey": 12,
  // ... 10+ more fields ...
}
```

**Delete Payload Structure** (3 fields only):
```json
{
  "Operation": "DeleteExpense",
  "expenseDeviceKey": 13120,              // SINGULAR key, not array
  "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6"
}
```

### Key Differences

| Aspect | Add/Update | Delete |
|--------|-----------|--------|
| Operation | "AddExpense", "UpdateExpense" | "DeleteExpense" |
| Expense ID | `expenseDeviceKeys` (array) | `expenseDeviceKey` (singular) |
| Expense Details | Full (amount, date, category, etc.) | None (just the key) |
| Field Count | 20+ | 3 |
| Payload Bytes | 660 (padded) | 104 actual |
| Base64 Length | 880 chars | 683 chars |

### Why Mobile Sync Failed

Mobile app's sync handler expects:
- **Delete operations**: Minimal payload with just operation type and key
- **Add/Update operations**: Full transaction details

The wrapper was sending full expense details for delete, which the mobile app rejected because:
1. Unexpected field `expenseDeviceKeys` (plural)
2. Unexpected fields like `amount`, `currency`, `category` in a delete operation
3. Payload structure mismatch caused processing error

---

## Fix Implementation

**Location**: [sync.py create_expense_update()](../../src/python/homebudget/sync.py#L34)

**Change**:
```python
def create_expense_update(self, expense, operation="AddExpense"):
    # DELETE operations have different payload - minimal structure
    if operation == "DeleteExpense":
        device = self._get_primary_device()
        payload = {
            "Operation": operation,
            "expenseDeviceKey": expense.key,        # Singular, not array
            "deviceId": device.device_id,
        }
    else:
        # ADD/UPDATE operations use full expense details
        device = self._get_primary_device()
        account_device = self._get_entity_device("Account", expense.account)
        # ... build full payload ...
```

**Impact**:
- ✓ Delete operations now generate correct minimal payload
- ✓ Delete SyncUpdate entries will have proper structure
- ✓ Mobile app sync handler will accept and process deletes
- ✓ Deletes now sync to mobile devices

---

## Lessons Learned

### From Issue 001 → Applied to Issue 002

**Issue 001** showed: Compression format and payload encoding must match native app exactly (took 2 phases of debugging)

**Issue 002** revealed: **Structural format** also matters - different operations require different JSON structures

### Investigation Methodology That Worked

1. **Hypothesis testing before jumping to conclusions** - We first tested the theory about updateType
2. **Payload decoding inspection** - Checked actual base64 → zlib → JSON pipeline  
3. **Comparative analysis** - Compared working (Add) vs broken (Delete) payloads
4. **Field-level inspection** - Identified structural differences at JSON field level

### What NOT to Do

- ❌ Assume all operations use same payload structure
- ❌ Test only local changes without inspecting database
- ❌ Skip payload decoding - decode and inspect the actual bytes
- ❌ Trust field names without verifying singular vs plural

---

## Diagnostic Tools

The systematic approach from 001 identified two distinct failure modes:

1. **Phase 1 Failure**: SyncUpdate entries not created at all
   - Diagnosis: Compare database snapshots, look for SyncUpdate rows
   - Resolution: Implement SyncUpdate creation in wrapper

2. **Phase 2 Failure**: SyncUpdate entries created but not synced
   - Diagnosis: Decode and inspect payload format, size, encoding
   - Resolution: Fix compression format and padding

**For delete failures, the same two modes apply**:
- Mode A: Delete creates SyncUpdate but payload format is wrong
- Mode B: Delete creates SyncUpdate with correct payload, but app doesn't process it

---

## Diagnostic Plan

### Phase 1: SyncUpdate Entry Validation

**Goal**: Confirm SyncUpdate entry for delete is created with correct structure

**Steps**:

1. **Extract delete SyncUpdate entry**:
   ```python
   # After delete operation, query SyncUpdate table
   SELECT key, updateType, uuid, payload FROM SyncUpdate 
   WHERE updateType = 'DeleteExpense' 
   ORDER BY key DESC LIMIT 1
   ```

2. **Compare with Add/Update payloads**:
   - Decode all three payloads (AddExpense, UpdateExpense, DeleteExpense)
   - Check for structural differences in JSON
   - Verify all required fields present in delete payload
   - Look for operation-specific fields

3. **Inspect delete payload structure**:
   ```json
   // Expected structure for DeleteExpense:
   {
     "op": "DeleteExpense",
     "key": 13120,
     "expenseDeviceKeys": [...],
     "deviceId": "...",
     // Should have minimal data since it's just deleting
   }
   ```

4. **Check payload format**:
   - Character count (should be 880 for all operations)
   - Base64 padding consistency with add/update
   - Decompress and verify JSON structure

---

### Phase 2: Sync Queue Processing

**Goal**: Determine if mobile app receives and processes delete operation

**Steps**:

1. **Monitor SyncUpdate table during sync**:
   - Run delete operation (creates SyncUpdate entry)
   - Connect to WiFi to trigger sync
   - Query SyncUpdate table after sync completes
   - Check if delete entry is removed (consumed) or remains

2. **Check mobile app state**:
   - Verify if deletion persists on mobile even after sync
   - Check mobile app logs for any errors processing delete
   - Compare expense count before/after sync on mobile

3. **Inspect device identifiers in delete payload**:
   - Check if deviceId, expenseDeviceKeys match mobile device keys
   - Verify device identifiers are consistent across add/update/delete
   - Look for device key mismatches that could cause rejection

---

### Phase 3: Database State Analysis

**Goal**: Verify expense is properly marked/removed as deleted

**Steps**:

1. **Check Expense table after delete**:
   ```python
   # Should expense be removed entirely, or marked with flag?
   SELECT * FROM Expense WHERE key = 13120
   # Check if row still exists after delete
   ```

2. **Check AccountTrans linkage**:
   ```python
   # Look for corresponding AccountTrans entry
   SELECT * FROM AccountTrans 
   WHERE transType = 1 AND transKey = 13120
   ```

3. **Check if soft delete flags exist**:
   - Look for `deleteFlag`, `isDeleted`, `status` columns
   - Check if delete operation should mark row instead of removing

---

## Comparison Matrix: Add vs Update vs Delete

| Aspect | AddExpense | UpdateExpense | DeleteExpense |
|--------|-----------|---------------|---------------|
| SyncUpdate created | ✓ Yes | ✓ Yes | ✓ Yes |
| Payload character count | 880 | 880 | ? |
| Device keys in payload | ✓ Present | ✓ Present | ? |
| Syncs to mobile | ✓ Yes | ✓ Yes | ✗ No |
| Database row consumed | N/A | Still exists (updated) | Should be removed |

---

## Hypothesis Testing Order

1. **Hypothesis A**: Delete payload has formatting issue (wrong size/encoding)
   - Test: Decode delete payload, compare with add/update
   - Validation: All three should be 880 chars, same encoding
   - Script: `python tests/manual/inspect_delete_sync.py --compare`

2. **Hypothesis B**: Delete payload has wrong structure for DELETE operations
   - Test: Compare JSON structure - does delete need fewer/different fields than add?
   - Issue from 001: Payload format must match native app exactly
   - Action: Create test delete in native app, capture payload, compare with wrapper
   - Expected: Wrapper delete payload structure should match native app delete payload

3. **Hypothesis C**: Delete payload missing "Operation" field or has wrong field name
   - Test: Check if "Operation": "DeleteExpense" is present
   - Compare: AddExpense, UpdateExpense have same Operation field format
   - Issue from 001: Native app uses specific field names, getting one wrong breaks sync
   - Validation: Decode and inspect JSON, check field names match exactly

4. **Hypothesis D**: Mobile app receives delete but cannot process it
   - Test: Check mobile logs for delete operation handling
   - Test: Verify expense still exists and can be modified on mobile
   - Validation: Mobile logs show delete attempt and error/outcome
   - Serial #: Must perform after confirming payload format is correct

5. **Hypothesis E**: Expense row should use soft delete, not hard delete
   - Test: Inspect database schema for delete flag columns
   - Test: Compare wrapper deletion with native app deletion
   - Validation: Both methods should match
   - Note: Hard delete immediately removes row, soft delete marks with flag

---

## Key Diagnostic Commands

```bash
# Compare delete payload against add and update payloads
python tests/manual/inspect_delete_sync.py --compare

# Inspect specific delete operation
python -c "
import sqlite3
from tests.manual.inspect_delete_sync import decode_payload

db = sqlite3.connect('path/to/homebudget.db')
db.row_factory = sqlite3.Row

# Get all operations in order
ops = db.execute(
    '''SELECT key, payload FROM SyncUpdate 
       WHERE payload IS NOT NULL 
       ORDER BY key DESC LIMIT 50'''
).fetchall()

for op in ops:
    try:
        decoded = decode_payload(op['payload'])
        op_type = decoded.get('Operation', 'Unknown')
        print(f\"Key {op[0]}: {op_type} (expense {decoded.get('expenseDeviceKeys', ['?'])[0]})\")
    except Exception as e:
        print(f\"Key {op[0]}: ERROR - {e}\")
"

# Check what fields exist in delete vs add payloads
python -c "
import json
from tests.manual.inspect_delete_sync import decode_payload
import sqlite3

db = sqlite3.connect('path/to/homebudget.db')

# We need the actual payloads, so extract them
# ... (see inspect_delete_sync.py for full implementation)
"
```

## Diagnostic Tools

### 1. Diagnostic Delete Sync Test
Runs CRUD operations and captures sync state at each step:

```bash
python tests/manual/diagnostic_delete_sync.py
```

**Output includes**:
- Before/after SyncUpdate state per operation
- Operation type, updateType field, and payload length
- Decoded JSON structure for each operation
- Comparison table showing differences

### 2. Payload Inspection Script
Compares Add, Update, Delete operation payloads:

```bash
python tests/manual/inspect_delete_sync.py --compare
```

**Shows**:
- Payload character counts (should all be 880)
- Field differences between operations
- Highlighted warnings for anomalies

### 3. Manual Test with Verification
Full UAT test with sync validation:

```bash
python tests/manual/manual_test_runner.py --test-id uat_expense_crud
```

**Steps**:
1. Create expense (verify syncs to mobile)
2. Update expense (verify syncs to mobile)
3. Delete expense (verify syncs to mobile) ← **This is failing**

### 4. Direct Database Query
Inspect SyncUpdate table:

```bash
python -c "
import sqlite3
db = sqlite3.connect('path/to/homebudget.db')
rows = db.execute(
    'SELECT key, updateType, LENGTH(payload) FROM SyncUpdate ORDER BY key DESC LIMIT 5'
).fetchall()
for row in rows:
    print(f'SyncUpdate {row[0]}: type={row[1]}, payload_len={row[2]}')
"
```

---

## Learnings from Issue 001

### Step 0: Capture baseline (before delete test)
```bash
python tests/manual/manual_test_runner.py --test-id uat_expense_crud
# Stop at step where record exists and can be queried
```

### Step 1: Run comparison analysis
```bash
python tests/manual/inspect_delete_sync.py --compare
```

**Expected output format**:
```
AddExpense:
  Payload length: 880 chars
  JSON fields:
    Operation: 'AddExpense'
    expenseDeviceKeys: [13120]
    [... other fields ...]

UpdateExpense:
  Payload length: 880 chars  
  JSON fields:
    Operation: 'UpdateExpense'
    expenseDeviceKeys: [13120]
    [... same fields as Add? ...]

DeleteExpense:
  Payload length: ??? chars (should be 880)
  JSON fields:
    Operation: 'DeleteExpense'
    expenseDeviceKeys: [13120]
    [... which fields should be present? ...]
```

**Analysis**:
- If Delete payload is NOT 880 chars → **Encoding issue** (Hypothesis A)
- If Delete missing required fields → **Incomplete payload** (Hypothesis B)  
- If Delete has different field values → **Data mismatch** (Hypothesis C)

### Step 2: Inspect database state after delete
```bash
python -c "
import sqlite3
db = sqlite3.connect('path/to/homebudget.db')

# Check if expense row still in database
expense = db.execute('SELECT * FROM Expense WHERE key = 13120').fetchone()
print(f'Expense row exists: {expense is not None}')

# Check if sync entry was consumed
log_entries = db.execute(
    '''SELECT COUNT(*) FROM SyncUpdate 
       WHERE payload LIKE \"%expenseDeviceKeys%13120%\"'''
).fetchone()
print(f'Delete sync entries: {log_entries[0]}')
"
```

### Step 3: Check mobile app logs
- Connect mobile device
- Look for error messages when receiving delete sync
- Check if app shows the deleted expense or if it persists

### Step 4: Verify fix in native app
- Manually delete expense in HomeBudget mobile app
- Inspect resulting SyncUpdate entry
- Compare payload with wrapper-generated delete payload
```

---

## Success Criteria

- [ ] Delete SyncUpdate payload has same structure/format as add/update
- [ ] Payload character count is 880 (consistent encoding)
- [ ] All device identifiers present and correct
- [ ] SyncUpdate entry consumed (removed) after sync completes
- [ ] Mobile app shows expense deleted after sync
- [ ] Expense cannot be modified or retrieved on mobile
