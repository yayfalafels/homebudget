# Sync Update Mechanism

## Table of contents

- [Overview](#overview)
- [SyncUpdate table structure](#syncupdate-table-structure)
- [Payload encoding and decoding](#payload-encoding-and-decoding)
- [Operation types](#operation-types)
- [AddExpense operation structure](#addexpense-operation-structure)
- [Device identifiers](#device-identifiers)
- [Wrapper integration design](#wrapper-integration-design)
- [Implementation requirements](#implementation-requirements)

## Overview

HomeBudget uses the SyncUpdate table as a queue for pending sync operations. When a transaction is created, updated, or deleted through the application UI, a corresponding entry is written to SyncUpdate with an encoded JSON payload that describes the operation. The sync service reads these entries, uploads them to the sync server, and removes them from the queue after successful sync.

The wrapper must mimic this behavior by inserting SyncUpdate entries for each transaction it creates to ensure changes propagate to other devices in the sync group.

## SyncUpdate table structure

| Column | Type | Description |
| --- | --- | --- |
| key | INTEGER | Primary key, auto-incremented |
| updateType | TEXT | Operation category, typically "Any" |
| uuid | TEXT | Unique identifier for the operation |
| payload | TEXT | Base64 encoded and zlib compressed JSON payload |

Source: [docs/sqlite-schema.md](sqlite-schema.md#syncupdate)

## Payload encoding and decoding

The payload field follows a three-step encoding process:

1. Serialize operation to JSON string
2. Compress with zlib using raw deflate
3. Encode compressed bytes with base64

Decoding reverses this process:

1. Decode base64 to raw bytes
2. Decompress with zlib using `wbits=-zlib.MAX_WBITS` for raw deflate
3. Parse JSON string to operation object

Base64 padding may be required for proper decoding. The encoder uses standard base64 with padding stripped, so the decoder must add padding as needed when the payload length is not a multiple of 4.

Reference implementation: [.dev/.scripts/python/decode_syncupdate_payloads.py](.dev/.scripts/python/decode_syncupdate_payloads.py)

## Operation types

Observed operation types from diagnostics:

| Operation | Description | Related tables |
| --- | --- | --- |
| AddExpense | Create new expense transaction | Expense, AccountTrans |
| AddIncome | Create new income transaction | Income, AccountTrans |
| AddTransfer | Create new transfer transaction | Transfer, AccountTrans |
| AddBudgetHistory | Create budget history entry | BudgetHistory |
| SetBudget2 | Update budget settings | BudgetSettings |

The wrapper must support at minimum AddExpense, AddIncome, and AddTransfer to cover CRUD operations for transactions.

## AddExpense operation structure

Decoded AddExpense payload from test expense with key 13073:

```json
{
  "periods": 1,
  "Operation": "AddExpense",
  "accountDeviceKey": 3,
  "timeStamp": "2026-02-16 10:36:25",
  "expenseDeviceKeys": [13073],
  "currencyAmount": "25",
  "billDeviceKey": 0,
  "billDeviceId": "",
  "expenseDateString": "2026-02-16",
  "receiptImageNeedsSaving": "False",
  "currency": "SGD",
  "categoryDeviceKey": 12,
  "amount": 25,
  "accountDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
  "notesString": "test",
  "payeeDeviceId": "",
  "recurringKey": 0,
  "payeeDeviceKey": 0,
  "subcategoryDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
  "subcategoryDeviceKey": 49,
  "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6",
  "categoryDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674"
}
```

Key fields:

- `expenseDeviceKeys`: Array of Expense.key values for the transaction
- `deviceId`: Device identifier from DeviceInfo for the originating device
- `accountDeviceId`, `categoryDeviceId`, `subcategoryDeviceId`: Device identifiers for related entities
- `timeStamp`: Transaction timestamp in local time, format `YYYY-MM-DD HH:MM:SS`
- `currencyAmount`: String representation of foreign currency amount
- `amount`: Numeric amount in account base currency

Source: [.dev/logs/sync-diagnostics/payloads/syncupdate_before_9.txt](.dev/logs/sync-diagnostics/payloads/syncupdate_before_9.txt)

## Device identifiers

Device identifiers link operations to specific devices in the sync group. The wrapper must populate these fields to match the behavior of the native application.

### DeviceInfo reference

The primary device for the wrapper should be identified in DeviceInfo with `isPrimary = 'Y'`. For the test database:

| key | deviceId | deviceName | isActive | isPrimary |
| --- | --- | --- | --- | --- |
| 11 | 448cc747-79b2-46bf-93e2-4f62a91d4fe6 | DELLLatitude | Y | Y |

The wrapper must query DeviceInfo to locate the primary active device and use its deviceId for all SyncUpdate operations.

### Entity device identifiers

Categories, subcategories, accounts, and payees have associated deviceId and deviceKey fields. These typically match a reference device in the sync group. From the test expense:

- `categoryDeviceId`: A6F3C991-022C-407C-99B1-6E9402E8D674
- `categoryDeviceKey`: 12

The wrapper should query these identifiers from the respective entity tables when constructing the payload.

## Wrapper integration design

The wrapper should implement a SyncUpdateManager class that handles SyncUpdate insertion for all transaction operations.

### Class interface

```python
class SyncUpdateManager:
    def __init__(self, connection: sqlite3.Connection):
        """Initialize with database connection."""
        
    def create_expense_update(
        self,
        expense_key: int,
        expense_data: dict,
    ) -> int:
        """Create SyncUpdate entry for new expense.
        
        Returns:
            SyncUpdate.key for the created entry
        """
        
    def create_income_update(
        self,
        income_key: int,
        income_data: dict,
    ) -> int:
        """Create SyncUpdate entry for new income."""
        
    def create_transfer_update(
        self,
        transfer_key: int,
        transfer_data: dict,
    ) -> int:
        """Create SyncUpdate entry for new transfer."""
```

### Workflow integration

Transaction creation workflow with sync support:

1. Begin database transaction
2. Insert Expense, Income, or Transfer row
3. Insert related AccountTrans rows
4. Query device identifiers from DeviceInfo and entity tables
5. Construct operation payload with all required fields
6. Encode payload using zlib and base64
7. Insert SyncUpdate row with encoded payload and generated UUID
8. Commit database transaction

If any step fails, the entire transaction is rolled back to maintain consistency.

## Implementation requirements

### Required fields for AddExpense

- `Operation`: "AddExpense"
- `expenseDeviceKeys`: Array with Expense.key
- `deviceId`: Primary device identifier from DeviceInfo
- `timeStamp`: Transaction timestamp from Expense.timeStamp
- `expenseDateString`: Transaction date from Expense.date
- `accountDeviceKey`: Account key from Expense.payFrom
- `accountDeviceId`: Device identifier from Account table
- `categoryDeviceKey`: Category key from Expense.catKey
- `categoryDeviceId`: Device identifier from Category table
- `subcategoryDeviceKey`: Subcategory key from Expense.subCatKey
- `subcategoryDeviceId`: Device identifier from SubCategory table
- `amount`: Numeric amount from Expense.amount
- `currency`: Currency code from Expense.currency
- `currencyAmount`: String amount from Expense.currencyAmount
- `notesString`: Notes from Expense.notes
- `payeeDeviceKey`: Payee key from Expense.payeeKey or 0
- `payeeDeviceId`: Device identifier from Payee table or empty string
- `billDeviceKey`: Bill key from Expense.billKey or 0
- `billDeviceId`: Device identifier from Bill table or empty string
- `recurringKey`: Recurring key from Expense.recurringKey or 0
- `periods`: Number of periods, typically 1
- `receiptImageNeedsSaving`: "False" for wrapper transactions

### UUID generation

Generate a new UUID v4 for each SyncUpdate entry using standard UUID libraries. The UUID must be unique across all SyncUpdate entries in the database.

### Encoding implementation

```python
import base64
import json
import uuid
import zlib

def encode_payload(operation: dict) -> str:
    """Encode operation to SyncUpdate payload format."""
    json_str = json.dumps(operation, separators=(',', ':'))
    compressed = zlib.compress(json_str.encode('utf-8'), level=9)
    # Use raw deflate by stripping zlib header and checksum
    raw_deflate = compressed[2:-4]
    encoded = base64.b64encode(raw_deflate).decode('ascii')
    # Strip padding for consistency with native app
    return encoded.rstrip('=')

def generate_uuid() -> str:
    """Generate UUID for SyncUpdate entry."""
    return str(uuid.uuid4())
```

### Transaction safety

All SyncUpdate inserts must occur within the same database transaction as the related Expense, Income, or Transfer insert to ensure atomicity. If the SyncUpdate insert fails, the entire transaction should be rolled back.

### Testing strategy

1. Create test expense through wrapper with sync support enabled
2. Verify SyncUpdate entry is created with correct payload structure
3. Decode payload and validate all required fields match Expense data
4. Enable wifi and verify sync completes successfully
5. Confirm transaction appears on other devices in sync group

### Error handling

- If DeviceInfo query returns no primary device, raise configuration error
- If entity device identifiers are missing, use empty string for deviceId and 0 for deviceKey
- If payload encoding fails, log error and raise encoding exception
- If SyncUpdate insert fails, roll back entire transaction

## References

- [Issue 001 Sync Detection Diagnostics](issues/001-sync-detection-diagnostics.md)
- [SQLite Schema Reference](sqlite-schema.md)
- [Step 3 Schema and Data Model Mapping](develop/plan-wrapper-design-step3.md)
