"""Database schema constants."""

from __future__ import annotations

FLAG_Y = "Y"
FLAG_N = "N"

DEFAULT_PERIODS = 1
DEFAULT_MASTER_KEY = -1
DEFAULT_PAYEE_KEY = 0
DEFAULT_BILL_KEY = 0
DEFAULT_RECURRING_KEY = 0
DEFAULT_CATEGORY_SPLIT = FLAG_N
DEFAULT_IS_DETAIL_ENTRY = FLAG_Y
DEFAULT_INCLUDES_RECEIPT = FLAG_N
DEFAULT_CHECKED = FLAG_N

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
