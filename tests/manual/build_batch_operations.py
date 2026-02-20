#!/usr/bin/env python
"""Build batch operation JSON files for manual tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPENSE_DATE = "2026-02-20"
INCOME_DATE = "2026-02-20"
TRANSFER_DATE = "2026-02-20"

EXPENSE_CATEGORY = "Food (Basic)"
EXPENSE_SUBCATEGORY = "Cheap restaurant"
EXPENSE_ACCOUNT = "TWH - Personal"
EXPENSE_AMOUNT = "22.50"
EXPENSE_NOTES_ADD = "UAT Batch Step1 Expense Add"
EXPENSE_NOTES_UPDATE = "UAT Batch Step2 Expense Update"

INCOME_NAME = "Profit and Loss"
INCOME_ACCOUNT = "TWH IB USD"
INCOME_AMOUNT = "1200.00"
INCOME_NOTES_ADD = "UAT Batch Step3 Income Add"
INCOME_NOTES_UPDATE = "UAT Batch Rollback Income Update"

TRANSFER_FROM = "TWH - Personal"
TRANSFER_TO = "30 CC Hashemis"
TRANSFER_AMOUNT = "75.00"
TRANSFER_NOTES_ADD = "UAT Batch Step3 Transfer Add"
TRANSFER_NOTES_UPDATE = "UAT Batch Rollback Transfer Update"


def _build_step1() -> list[dict[str, object]]:
    return [
        {
            "resource": "expense",
            "operation": "add",
            "parameters": {
                "date": EXPENSE_DATE,
                "category": EXPENSE_CATEGORY,
                "subcategory": EXPENSE_SUBCATEGORY,
                "amount": EXPENSE_AMOUNT,
                "account": EXPENSE_ACCOUNT,
                "notes": EXPENSE_NOTES_ADD,
            },
        }
    ]


def _build_step2(expense_key: int) -> list[dict[str, object]]:
    return [
        {
            "resource": "expense",
            "operation": "update",
            "parameters": {
                "key": expense_key,
                "notes": EXPENSE_NOTES_UPDATE,
            },
        }
    ]


def _build_step3(expense_key: int) -> list[dict[str, object]]:
    return [
        {
            "resource": "expense",
            "operation": "delete",
            "parameters": {
                "key": expense_key,
            },
        },
        {
            "resource": "income",
            "operation": "add",
            "parameters": {
                "date": INCOME_DATE,
                "name": INCOME_NAME,
                "amount": INCOME_AMOUNT,
                "account": INCOME_ACCOUNT,
                "notes": INCOME_NOTES_ADD,
            },
        },
        {
            "resource": "transfer",
            "operation": "add",
            "parameters": {
                "date": TRANSFER_DATE,
                "from_account": TRANSFER_FROM,
                "to_account": TRANSFER_TO,
                "amount": TRANSFER_AMOUNT,
                "notes": TRANSFER_NOTES_ADD,
            },
        },
    ]


def _build_rollback(income_key: int, transfer_key: int) -> list[dict[str, object]]:
    return [
        {
            "resource": "income",
            "operation": "update",
            "parameters": {
                "key": income_key,
                "notes": INCOME_NOTES_UPDATE,
            },
        },
        {
            "resource": "income",
            "operation": "delete",
            "parameters": {
                "key": income_key,
            },
        },
        {
            "resource": "transfer",
            "operation": "update",
            "parameters": {
                "key": transfer_key,
                "notes": TRANSFER_NOTES_UPDATE,
            },
        },
        {
            "resource": "transfer",
            "operation": "delete",
            "parameters": {
                "key": transfer_key,
            },
        },
    ]


def build_payload(mode: str, expense_key: int | None, income_key: int | None, transfer_key: int | None) -> list[dict[str, object]]:
    if mode == "step1":
        return _build_step1()
    if mode == "step2":
        if expense_key is None:
            raise ValueError("expense_key is required for step2")
        return _build_step2(expense_key)
    if mode == "step3":
        if expense_key is None:
            raise ValueError("expense_key is required for step3")
        return _build_step3(expense_key)
    if mode == "rollback":
        if income_key is None or transfer_key is None:
            raise ValueError("income_key and transfer_key are required for rollback")
        return _build_rollback(income_key, transfer_key)
    raise ValueError(f"Unknown mode: {mode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build batch operation JSON files.")
    parser.add_argument("--mode", required=True, choices=["step1", "step2", "step3", "rollback"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expense-key", type=int)
    parser.add_argument("--income-key", type=int)
    parser.add_argument("--transfer-key", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args.mode, args.expense_key, args.income_key, args.transfer_key)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Wrote batch operations to {args.output}")


if __name__ == "__main__":
    main()
