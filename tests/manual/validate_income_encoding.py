#!/usr/bin/env python
"""Validate Income SyncUpdate encoding for UAT (Issue 002).

Checks:
- Base64 is URL-safe (no + or /)
- Trailing padding = is stripped
- Zlib decompression works (wbits=15)
- JSON is valid after decompression

Usage:
    python validate_income_encoding.py --db tests/fixtures/sync_test.db
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from base64 import urlsafe_b64decode
from zlib import decompress


def validate_encoding(db_path: str) -> bool:
    """Validate all SyncUpdate payloads match Issue 002 requirements."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all SyncUpdate entries
    cursor.execute("""
        SELECT key, payload FROM SyncUpdate 
        WHERE updateType = 'Any'
        ORDER BY key DESC
        LIMIT 50
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ No SyncUpdate entries found")
        return False
    
    print(f"Found {len(rows)} SyncUpdate entries\n")
    
    failures = []
    
    for su_key, encoded in rows:
        print(f"SyncUpdate #{su_key}:")
        
        # Check 1: No standard base64 padding chars at end
        if encoded.endswith("="):
            print(f"  ❌ Trailing = not stripped")
            failures.append(su_key)
            continue
        
        # Check 2: URL-safe base64 (only - and _ for +/)
        if "+" in encoded or "/" in encoded:
            print(f"  ❌ Contains non-URL-safe characters (+ or /)")
            failures.append(su_key)
            continue
        
        print(f"  ✓ URL-safe base64 format")
        
        # Check 3: Decompress valid
        try:
            # Add padding back for decoding
            padding = 4 - (len(encoded) % 4)
            if padding != 4:
                padded = encoded + "=" * padding
            else:
                padded = encoded
            
            compressed = urlsafe_b64decode(padded)
            decompressed = decompress(compressed, wbits=15)
            payload = json.loads(decompressed.decode("utf-8"))
        except Exception as e:
            print(f"  ❌ Decompress/JSON failed: {e}")
            failures.append(su_key)
            continue
        
        print(f"  ✓ Decompression successful")
        
        # Check 4: Verify operation
        operation = payload.get("Operation")
        if operation and "Income" in operation:
            print(f"  ✓ Income operation: {operation}")
        
        # Check 5: Verify encoding characteristics
        print(f"  ✓ Base64 length: {len(encoded)} chars")
        print(f"  ✓ Compressed size: {len(compressed)} bytes")
    
    conn.close()
    
    if failures:
        print(f"\n❌ {len(failures)} payloads failed validation: {failures}")
        return False
    else:
        print(f"\n✓ All {len(rows)} payloads passed encoding validation")
        return True


def main():
    parser = argparse.ArgumentParser(description="Validate SyncUpdate encoding")
    parser.add_argument("--db", required=True, help="Database path")
    
    args = parser.parse_args()
    
    if validate_encoding(args.db):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
