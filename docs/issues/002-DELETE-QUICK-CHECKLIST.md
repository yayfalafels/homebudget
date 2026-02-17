# Issue 002: Delete Sync Quick Reference

## Root Cause (Resolved 2026-02-17)
**DELETE operations require completely different payload structure than ADD/UPDATE**

## Issue Timeline
1. ✓ Fixed updateType hardcoding (was "Any", now uses operation type)
2. ✓ Discovered updateType fix not sufficient
3. ✓ **ROOT CAUSE FOUND**: Delete operations need minimal 3-field payload vs full 20+ field payload for Add/Update

## Fix Applied

### Problem
Wrapper was generating full expense payload for DELETE operations:
```json
{
  "Operation": "DeleteExpense",
  "expenseDeviceKeys": [13120],      // WRONG: plural array
  "amount": 25.50,                   // WRONG: unnecessary fields
  "categoryDeviceKey": 5,            // WRONG: unnecessary fields
  // ... 15+ more unnecessary fields
}
```

### Solution
Delete operations now use minimal payload:
```json
{
  "Operation": "DeleteExpense",
  "expenseDeviceKey": 13120,         // CORRECT: singular key
  "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6"
}
```

### Location
[sync.py create_expense_update() method](../../src/python/homebudget/sync.py#L34)

---

## Verification Steps

### Quick Test
```bash
# Run diagnostic script
python .dev/.scripts/python/show_delete_json.py

# Should show minimal 3-field JSON:
# {
#   "Operation": "DeleteExpense",
#   "expenseDeviceKey": [number],
#   "deviceId": "[uuid]"
# }
```

### Full UAT Test
```bash
python tests/manual/run_manual_tests.py uat_expense_crud
```

Expected results:
- ✓ Create: Expense created and syncs to mobile
- ✓ Read: Expense appears on mobile
- ✓ Update: Changes sync to mobile
- ✓ Delete: Expense deleted on both desktop and mobile

### Mobile Verification
After running test:
- Delete step should remove expense from mobile app
- Expense should not reappear after sync
- No error messages about "DeleteExpense"

---

## Payload Structure Comparison

| Aspect | Add/Update | Delete |
|--------|-----------|--------|
| Fields in JSON | 20+ | 3 |
| Base64 length | ~880 chars | ~683 chars |
| Compressed size | 660 bytes | 512 bytes |
| Expense ID field | `expenseDeviceKeys` (array) | `expenseDeviceKey` (singular) |
| Includes amount | Yes | No |
| Includes category | Yes | No |
| Includes date | Yes | No |

---

## Technical Details

### Why This Matters
Mobile app's sync handler has different code paths:
- **AddExpense** → Insert record with all fields
- **UpdateExpense** → Update record with new values  
- **DeleteExpense** → Remove record by key only

Sending full payload to DeleteExpense handler → fields not expected → processing error

### How We Discovered It
1. Inspected base64 → zlib → JSON pipeline
2. Compared working Add/Update payload vs broken Delete payload
3. Found structural differences in actual database entries
4. Modified sync.py to branch on operation type

---

## Related Documentation
- [002-delete-sync-diagnostics.md](002-delete-sync-diagnostics.md) - Full diagnostic analysis
- [sync.py](../../src/python/homebudget/sync.py) - Modified source
- [Issue 001 Notes](001-sync-encoding-fix.md) - Payload encoding methodology

---
