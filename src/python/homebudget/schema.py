from __future__ import annotations

EXPENSE_COLUMNS = [
    "key",
    "date",
    "catKey",
    "subCatKey",
    "amount",
    "periods",
    "notes",
    "isDetailEntry",
    "masterKey",
    "includesReceipt",
    "payFrom",
    "payeeKey",
    "billKey",
    "deviceIdKey",
    "deviceKey",
    "timeStamp",
    "currency",
    "currencyAmount",
    "recurringKey",
    "isCategorySplit",
]

TRANSACTION_TYPES = {
    "balance": 0,
    "expense": 1,
    "income": 2,
    "transfer_out": 3,
    "transfer_in": 4,
}
