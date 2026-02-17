#!/usr/bin/env python
"""Inspect and validate delete payload decoding logic."""

from __future__ import annotations

import base64
from pathlib import Path
import sqlite3
import sys
import zlib
import json


def inspect_delete_payload(db_path: Path | None = None) -> None:
    """Inspect the delete SyncUpdate payload in detail."""
    if db_path is None:
        import os
        config_path = (
            Path(os.environ.get("USERPROFILE", ".")) 
            / "OneDrive" / "Documents" / "HomeBudgetData" / "homebudget.db"
        )
        if config_path.exists():
            db_path = config_path
        else:
            raise ValueError("Database path required")
    
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    
    # Get latest three operations
    rows = db.execute(
        """SELECT key, updateType, payload FROM SyncUpdate 
           WHERE updateType IN ('AddExpense', 'UpdateExpense', 'DeleteExpense')
           ORDER BY key DESC LIMIT 3"""
    ).fetchall()
    
    if not rows:
        print("No SyncUpdate entries found")
        return
    
    operations = {}
    for row in rows:
        operations[row['updateType']] = row
    
    print("="*80)
    print("PAYLOAD DECODING ANALYSIS")
    print("="*80)
    
    for op_type in ["AddExpense", "UpdateExpense", "DeleteExpense"]:
        if op_type not in operations:
            print(f"\n{op_type}: NOT FOUND")
            continue
        
        row = operations[op_type]
        payload_str = row['payload']
        
        print(f"\n{op_type}:")
        print(f"  Raw payload length: {len(payload_str)} chars")
        
        try:
            # Step 1: Check base64 decoding
            print(f"\n  [1] Base64 Decoding:")
            # Add padding back
            padding_needed = 4 - (len(payload_str) % 4)
            padded = payload_str + "=" * padding_needed if padding_needed < 4 else payload_str
            print(f"      Padding needed: {padding_needed if padding_needed < 4 else 0}")
            
            try:
                compressed_bytes = base64.urlsafe_b64decode(padded)
                print(f"      ✓ Base64 decode successful")
                print(f"      Decompressed bytes length: {len(compressed_bytes)}")
            except Exception as e:
                print(f"      ✗ Base64 decode FAILED: {e}")
                continue
            
            # Step 2: Check zlib decompression
            print(f"\n  [2] Zlib Decompression:")
            try:
                decompressed = zlib.decompress(compressed_bytes, wbits=15)
                print(f"      ✓ Zlib decompress successful (wbits=15)")
                print(f"      Decompressed string length: {len(decompressed)} bytes")
            except Exception as e:
                print(f"      ✗ Zlib decompress FAILED: {e}")
                # Try other wbits values
                for wbits in [-15, 16+15, 32+15]:
                    try:
                        test = zlib.decompress(compressed_bytes, wbits=wbits)
                        print(f"      ⚠ Alternative wbits={wbits} SUCCESS (this is wrong!)")
                    except:
                        pass
                continue
            
            # Step 3: Check JSON parsing
            print(f"\n  [3] JSON Parsing:")
            try:
                json_str = decompressed.decode('utf-8')
                op_dict = json.loads(json_str)
                print(f"      ✓ JSON parse successful")
                print(f"      Fields ({len(op_dict)}): {', '.join(sorted(op_dict.keys())[:5])}...")
            except Exception as e:
                print(f"      ✗ JSON parse FAILED: {e}")
                print(f"      Raw decompressed (first 200 chars): {repr(decompressed[:200])}")
                continue
            
            # Step 4: Compare fields and values
            print(f"\n  [4] JSON Structure:")
            for key in sorted(op_dict.keys()):
                value = op_dict[key]
                if isinstance(value, (list, dict)):
                    print(f"      {key}: {type(value).__name__}({len(value)} items)")
                elif isinstance(value, str) and len(value) > 50:
                    print(f"      {key}: {repr(value[:50])}...")
                else:
                    print(f"      {key}: {repr(value)}")
        
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
    
    # Now compare structure
    print("\n" + "="*80)
    print("FIELD COMPARISON")
    print("="*80)
    
    all_payloads = {}
    for op_type in ["AddExpense", "UpdateExpense", "DeleteExpense"]:
        if op_type not in operations:
            continue
        
        try:
            row = operations[op_type]
            payload_str = row['payload']
            padded = payload_str + "=" * (4 - (len(payload_str) % 4)) if len(payload_str) % 4 else payload_str
            compressed = base64.urlsafe_b64decode(padded)
            decompressed = zlib.decompress(compressed, wbits=15)
            all_payloads[op_type] = json.loads(decompressed.decode('utf-8'))
        except:
            pass
    
    if len(all_payloads) > 1:
        # Find all unique fields
        all_fields = set()
        for op_dict in all_payloads.values():
            all_fields.update(op_dict.keys())
        
        for field in sorted(all_fields):
            print(f"\n{field}:")
            for op_type in ["AddExpense", "UpdateExpense", "DeleteExpense"]:
                if op_type in all_payloads:
                    value = all_payloads[op_type].get(field, "MISSING")
                    if isinstance(value, str) and len(value) > 40:
                        print(f"  {op_type}: {repr(value[:40])}...")
                    else:
                        print(f"  {op_type}: {repr(value)}")
                else:
                    print(f"  {op_type}: NOT FOUND")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_delete_payload(Path(sys.argv[1]))
    else:
        inspect_delete_payload()
