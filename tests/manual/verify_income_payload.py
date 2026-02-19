#!/usr/bin/env python
"""Verify Income SyncUpdate payload structure for UAT.

Usage:
    python verify_income_payload.py --db tests/fixtures/sync_test.db \
        --operation AddIncome --expected-key 1500
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from base64 import urlsafe_b64decode
from zlib import decompress

def verify_payload(db_path: str, operation: str, expected_key: int) -> bool:
    """Verify the latest income payload matches expected operation."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get latest SyncUpdate
    cursor.execute("""
        SELECT payload FROM SyncUpdate 
        ORDER BY key DESC LIMIT 1
    """)
    row = cursor.fetchone()
    
    if not row:
        print("❌ No SyncUpdate entries found")
        return False
    
    encoded = row[0]
    
    # Decode payload
    try:
        parsed = encoded + "=" * (4 - len(encoded) % 4)  # Add padding back
        compressed = urlsafe_b64decode(parsed)
        decompressed = decompress(compressed, wbits=15)
        payload = json.loads(decompressed.decode("utf-8"))
    except Exception as e:
        print(f"❌ Failed to decode payload: {e}")
        return False
    
    print(f"✓ Payload decoded successfully")
    print(f"  Operation: {payload.get('Operation')}")
    
    # Verify operation
    if payload.get("Operation") != operation:
        print(f"❌ Operation mismatch: expected {operation}, got {payload.get('Operation')}")
        return False
    
    print(f"✓ Operation verified: {operation}")
    
    # Verify key field
    key_field = "deviceKey"  # Income uses deviceKey
    actual_key = payload.get(key_field)
    
    if not isinstance(actual_key, int):
        print(f"❌ {key_field} is not integer: {actual_key}")
        return False
    
    if actual_key != expected_key:
        print(f"❌ {key_field} mismatch: expected {expected_key}, got {actual_key}")
        return False
    
    print(f"✓ {key_field} verified: {actual_key}")
    
    # For Add/Update, verify required fields
    if operation in ("AddIncome", "UpdateIncome"):
        required_fields = {"Operation", "deviceId", key_field, "amount", "currency", "name"}
        missing = required_fields - set(payload.keys())
        if missing:
            print(f"❌ Missing required fields: {missing}")
            return False
        print(f"✓ All required fields present")
    
    # For Delete, verify minimal structure
    if operation == "DeleteIncome":
        required_fields = {"Operation", "deviceId", key_field}
        missing = required_fields - set(payload.keys())
        if missing:
            print(f"❌ Missing required fields: {missing}")
            return False
        print(f"✓ Delete payload structure verified (3 fields)")
    
    print(f"\nFull payload:")
    print(json.dumps(payload, indent=2))
    
    conn.close()
    return True


def main():
    parser = argparse.ArgumentParser(description="Verify Income SyncUpdate payload")
    parser.add_argument("--db", required=True, help="Database path")
    parser.add_argument("--operation", required=True, help="Operation type (AddIncome, UpdateIncome, DeleteIncome)")
    parser.add_argument("--expected-key", type=int, required=True, help="Expected income key")
    
    args = parser.parse_args()
    
    if verify_payload(args.db, args.operation, args.expected_key):
        print("\n✓ Payload verification PASSED")
        return 0
    else:
        print("\n❌ Payload verification FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
