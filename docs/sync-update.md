# Sync Update Mechanism

## Table of contents

- [Overview](#overview)
- [Configuration driven payloads](#configuration-driven-payloads)
- [SyncUpdate table structure](#syncupdate-table-structure)
- [Encoding and decoding](#encoding-and-decoding)
- [Payload structure by operation](#payload-structure-by-operation)
- [Update operations and attribute fan out](#update-operations-and-attribute-fan-out)
- [Device identifiers](#device-identifiers)
- [Wrapper integration flow](#wrapper-integration-flow)
- [References](#references)

## Overview

HomeBudget uses the SyncUpdate table as a queue for pending sync operations. When a transaction is created, updated, or deleted through the application UI, a corresponding entry is written to SyncUpdate with an encoded JSON payload that describes the operation. The sync service reads these entries, uploads them to the sync server, and removes them from the queue after successful sync.

The wrapper mirrors this behavior by inserting SyncUpdate entries for each transaction it creates or updates so changes propagate to other devices in the sync group.

## Configuration driven payloads

Sync payloads are configuration driven. The wrapper reads [src/python/homebudget/sync-config.json](https://github.com/yayfalafels/homebudget/blob/main/src/python/homebudget/sync-config.json) to define payload fields, key formats, and compression rules per operation.

Key configuration concepts:

- Each resource has per operation field lists and compression rules.
- Key fields can be singular or array, depending on the operation.
- Padding rules are operation specific and may apply only to smaller payloads.

The implementation that loads and applies the configuration is in [src/python/homebudget/sync.py](https://github.com/yayfalafels/homebudget/blob/main/src/python/homebudget/sync.py).

## SyncUpdate table structure

| Column | Type | Description |
| --- | --- | --- |
| key | INTEGER | Primary key, auto incremented |
| updateType | TEXT | Operation category, currently set to Any |
| uuid | TEXT | Unique identifier for the operation |
| payload | TEXT | Base64 encoded and zlib compressed JSON payload |

Source: [docs/sqlite-schema.md](sqlite-schema.md#syncupdate)

## Encoding and decoding

The payload field follows a multi step encoding process. Rules are defined per operation in the configuration.

### Encoding flow

1. Serialize the operation to compact JSON with no spaces
2. Compress with full zlib format using wbits 15 and compression level 9
3. If configured, pad with null bytes to a minimum size
4. Encode with URL safe base64 using - and _
5. Strip trailing = padding

### Decoding flow

1. Convert URL safe base64 to standard base64
2. Add = padding if needed for a multiple of four length
3. Decode base64 to binary
4. Strip trailing null bytes that were used for minimum size padding
5. Decompress with full zlib format using wbits 15
6. Parse the UTF 8 JSON string

Key learnings:

- Full zlib format is required, raw deflate fails for native payloads.
- URL safe base64 is required and trailing = must be stripped.
- Padding is operation specific, not a fixed payload length.

Reference implementations:

- Encoder: [src/python/homebudget/sync.py](https://github.com/yayfalafels/homebudget/blob/main/src/python/homebudget/sync.py)
- Decoder: [tests/manual/verify_syncupdate.py](https://github.com/yayfalafels/homebudget/blob/main/tests/manual/verify_syncupdate.py)

## Payload structure by operation

The payload is operation specific. These examples mirror the current config and implementation. Fields shown are required for each operation.

### Expense operations

AddExpense uses an array key and full transaction detail fields.

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
    "amount": 25.0,
    "accountDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "notesString": "test",
    "payeeDeviceKey": 0,
    "payeeDeviceId": "",
    "recurringKey": 0,
    "subcategoryDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "subcategoryDeviceKey": 49,
    "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6",
    "categoryDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674"
}
```

UpdateExpense uses a singular key and the full set of update fields.

```json
{
    "Operation": "UpdateExpense",
    "accountDeviceKey": 3,
    "timeStamp": "2026-02-16 10:36:25",
    "expenseDeviceKey": 13073,
    "currencyAmount": "25",
    "expenseDateString": "2026-02-16",
    "receiptImageNeedsSaving": "False",
    "currency": "SGD",
    "categoryDeviceKey": 12,
    "amount": 25.0,
    "accountDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "notesString": "test",
    "payeeDeviceKey": 0,
    "payeeDeviceId": "",
    "subcategoryDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "subcategoryDeviceKey": 49,
    "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6",
    "categoryDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674"
}
```

DeleteExpense uses a minimal payload with a singular key.

```json
{
    "Operation": "DeleteExpense",
    "expenseDeviceKey": 13073,
    "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6"
}
```

### Income operations

AddIncome uses a singular key and a smaller payload with name and incomeText fields.

```json
{
    "Operation": "AddIncome",
    "accountDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "accountDeviceKey": 3,
    "amount": "125.00",
    "currency": "USD",
    "currencyAmount": "125.00",
    "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6",
    "deviceKey": 1401,
    "incomeText": "2026-02-17",
    "name": "Salary",
    "notes": "",
    "recurringKey": 0,
    "timeStamp": "2026-02-17 18:54:23"
}
```

UpdateIncome uses the same key format and updates the same field set.

```json
{
    "Operation": "UpdateIncome",
    "accountDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "accountDeviceKey": 3,
    "amount": "130.00",
    "currency": "USD",
    "currencyAmount": "130.00",
    "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6",
    "deviceKey": 1401,
    "incomeText": "2026-02-17",
    "name": "Salary",
    "notes": "",
    "timeStamp": "2026-02-17 19:02:05"
}
```

DeleteIncome uses a minimal payload with a singular key.

```json
{
    "Operation": "DeleteIncome",
    "deviceKey": 1401,
    "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6"
}
```

### Transfer operations

AddTransfer uses a singular key and includes from/to account details and forex amounts.

```json
{
    "Operation": "AddTransfer",
    "accountFromDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "accountFromDeviceKey": 3,
    "accountToDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "accountToDeviceKey": 5,
    "amount": "148.15",
    "currency": "SGD",
    "currencyAmount": "200.00",
    "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6",
    "deviceKey": 2001,
    "notes": "Transfer between accounts",
    "recurringKey": 0,
    "timeStamp": "2026-02-22 14:00:00",
    "transferDateString": "2026-02-22"
}
```

UpdateTransfer uses the same key format and updates the same field set.

```json
{
    "Operation": "UpdateTransfer",
    "accountFromDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "accountFromDeviceKey": 3,
    "accountToDeviceId": "A6F3C991-022C-407C-99B1-6E9402E8D674",
    "accountToDeviceKey": 5,
    "amount": "148.15",
    "currency": "SGD",
    "currencyAmount": "200.00",
    "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6",
    "deviceKey": 2001,
    "notes": "Updated transfer notes",
    "timeStamp": "2026-02-22 14:15:00",
    "transferDateString": "2026-02-22"
}
```

DeleteTransfer uses a minimal payload with a singular key.

```json
{
    "Operation": "DeleteTransfer",
    "deviceKey": 2001,
    "deviceId": "448cc747-79b2-46bf-93e2-4f62a91d4fe6"
}
```

## Update operations and attribute fan out

Update operations generate a SyncUpdate entry per changed attribute. The wrapper creates one SyncUpdate entry for each field change, using the full final record payload in each entry. This mirrors native behavior where a multi field update results in multiple sync events.

This behavior is implemented in `create_updates_for_changes` in [src/python/homebudget/sync.py](https://github.com/yayfalafels/homebudget/blob/main/src/python/homebudget/sync.py).

## Device identifiers

Device identifiers link operations to devices in the sync group. The wrapper resolves the primary device from DeviceInfo, then resolves entity device ids for related records such as Account, Category, and SubCategory.

Resolution details:

- Primary device is the first record with isPrimary and isActive set to Y.
- Entity device ids come from deviceIdKey values and are resolved in DeviceInfo.

## Wrapper integration flow

1. Begin a database transaction
2. Insert or update the resource record
3. Insert related AccountTrans rows when needed
4. Build the payload from sync-config.json
5. Encode the payload with the configured compression rules
6. Insert SyncUpdate row with updateType Any and a new UUID
7. Commit the transaction

If any step fails, the transaction is rolled back to keep the database consistent.

## References

- [SQLite Schema Reference](sqlite-schema.md)
