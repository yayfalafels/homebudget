from __future__ import annotations

from homebudget import schema


def test_expense_table_fields() -> None:
    expected = [
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

    assert schema.EXPENSE_COLUMNS == expected


def test_transaction_types() -> None:
    assert schema.TRANSACTION_TYPES == {
        "balance": 0,
        "expense": 1,
        "income": 2,
        "transfer_out": 3,
        "transfer_in": 4,
    }
