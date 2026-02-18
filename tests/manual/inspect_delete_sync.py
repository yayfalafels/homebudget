#!/usr/bin/env python
"""Diagnostic script to inspect delete operation SyncUpdate payloads."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sqlite3
import zlib


def decode_payload(payload_str: str) -> dict:
    """Decode a SyncUpdate payload to JSON."""
    # Add back padding
    payload_str = payload_str + "==" * (4 - len(payload_str) % 4)
    
    # Decode from URL-safe base64
    compressed = base64.urlsafe_b64decode(payload_str)
    
    # Decompress using full zlib format
    decompressed = zlib.decompress(compressed, wbits=15)
    
    # Parse JSON
    return json.loads(decompressed)


def compare_operations(db_path: Path) -> None:
    """Compare Add, Update, and Delete operation payloads."""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    
    operations = {}
    
    for op_name in ["AddExpense", "UpdateExpense", "DeleteExpense"]:
        row = db.execute(
            "SELECT key, payload FROM SyncUpdate WHERE payload IS NOT NULL ORDER BY key DESC LIMIT 20"
        ).fetchall()
        
        for record in row:
            try:
                payload_json = decode_payload(record["payload"])
                if payload_json.get("Operation") == op_name:
                    operations[op_name] = {
                        "sync_key": record["key"],
                        "payload": record["payload"],
                        "payload_len": len(record["payload"]),
                        "decoded": payload_json,
                    }
                    break
            except Exception as e:
                print(f"Failed to decode {op_name}: {e}")
    
    print("\n" + "="*80)
    print("OPERATION PAYLOAD COMPARISON")
    print("="*80)
    
    for op_name in ["AddExpense", "UpdateExpense", "DeleteExpense"]:
        if op_name not in operations:
            print(f"\n⚠️  {op_name}: NOT FOUND")
            continue
        
        op = operations[op_name]
        print(f"\n{op_name}:")
        print(f"  Payload length: {op['payload_len']} chars")
        print(f"  SyncUpdate key: {op['sync_key']}")
        print(f"  JSON fields:")
        
        decoded = op["decoded"]
        for key in sorted(decoded.keys()):
            value = decoded[key]
            if isinstance(value, (list, dict)):
                print(f"    {key}: {type(value).__name__} with {len(value)} items")
            else:
                print(f"    {key}: {repr(value)[:60]}")
    
    print("\n" + "="*80)
    print("FIELD DIFFERENCES")
    print("="*80)
    
    if len(operations) >= 2:
        all_keys = set()
        for op in operations.values():
            all_keys.update(op["decoded"].keys())
        
        for key in sorted(all_keys):
            values = {}
            for op_name, op in operations.items():
                if key in op["decoded"]:
                    values[op_name] = op["decoded"][key]
            
            # Check if value differs
            unique_values = set(str(v) for v in values.values())
            if len(unique_values) > 1:
                print(f"\n⚠️  {key}:")
                for op_name, value in sorted(values.items()):
                    print(f"    {op_name}: {repr(value)[:60]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect SyncUpdate payloads for delete operations"
    )
    parser.add_argument(
        "--db",
        type=Path,
        help="Path to HomeBudget database",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare Add, Update, Delete operations",
    )
    args = parser.parse_args()
    
    db_path = args.db
    if db_path is None:
        # Try default location
        import os
        config_path = (
            Path(os.environ.get("USERPROFILE", ".")) 
            / "OneDrive" / "Documents" / "HomeBudgetData" / "homebudget.db"
        )
        if config_path.exists():
            db_path = config_path
        else:
            raise ValueError("Database path required")
    
    if args.compare:
        compare_operations(db_path)
    else:
        print("Use --compare to compare operations")


if __name__ == "__main__":
    main()
