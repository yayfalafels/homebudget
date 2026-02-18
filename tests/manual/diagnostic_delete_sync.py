#!/usr/bin/env python
"""
Diagnostic test for delete operation sync issues.

This test creates, reads, updates, and deletes an expense while 
capturing detailed sync information at each step.

Usage:
    python tests/manual/diagnostic_delete_sync.py
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sqlite3
import sys
import zlib

from homebudget.client import HomeBudgetClient
from homebudget.models import ExpenseDTO
from decimal import Decimal
import datetime as dt


def decode_payload(payload_str: str) -> dict:
    """Decode a SyncUpdate payload to JSON."""
    payload_str = payload_str + "==" * (4 - len(payload_str) % 4)
    compressed = base64.urlsafe_b64decode(payload_str)
    decompressed = zlib.decompress(compressed, wbits=15)
    return json.loads(decompressed)


def capture_sync_state(db_path: Path) -> dict:
    """Capture current SyncUpdate table state."""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    
    rows = db.execute(
        "SELECT key, updateType, payload FROM SyncUpdate ORDER BY key DESC LIMIT 10"
    ).fetchall()
    
    syncs = []
    for row in rows:
        try:
            decoded = decode_payload(row["payload"]) if row["payload"] else {}
            syncs.append({
                "key": row["key"],
                "updateType": row["updateType"],
                "operation": decoded.get("Operation", "Unknown"),
                "payload_len": len(row["payload"]) if row["payload"] else 0,
                "decoded": decoded,
            })
        except Exception as e:
            syncs.append({
                "key": row["key"],
                "updateType": row["updateType"],
                "operation": "DECODE_ERROR",
                "error": str(e),
            })
    
    return {"syncs": syncs, "count": len(syncs)}


def print_sync_state(label: str, state: dict) -> None:
    """Print formatted sync state."""
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    
    syncs = state.get("syncs", [])
    if not syncs:
        print("(No SyncUpdate entries)")
        return
    
    for sync in syncs[:3]:  # Show latest 3
        print(f"\nSyncUpdate key={sync['key']}:")
        print(f"  updateType: {sync['updateType']}")
        print(f"  Operation: {sync['operation']}")
        print(f"  Payload length: {sync.get('payload_len', 'N/A')} chars")
        
        if "decoded" in sync and sync.get("operation") not in ["Unknown", "DECODE_ERROR"]:
            decoded = sync["decoded"]
            print(f"  Fields: {', '.join(sorted(decoded.keys()))[:60]}...")


def run_diagnostic(db_path: Path | None = None) -> None:
    """Run diagnostic test for delete sync."""
    if db_path is None:
        import os
        from homebudget.client import HomeBudgetClient
        # Resolve using same logic as client
        try:
            with HomeBudgetClient() as client:
                db_path = client.db_path
        except Exception:
            raise ValueError("Cannot find database path")
    
    print("Delete Operation Sync Diagnostic")
    print(f"Database: {db_path}")
    
    try:
        with HomeBudgetClient(db_path=db_path) as client:
            # Capture initial state
            initial_state = capture_sync_state(db_path)
            print_sync_state("INITIAL STATE (before operations)", initial_state)
            
            # Create test expense
            print("\n[1] Creating test expense...")
            expense_to_create = ExpenseDTO(
                date=dt.date.today(),
                category="Food (Basic)",
                subcategory="Cheap restaurant",
                amount=Decimal("25.50"),
                account="TWH - Personal",
                notes="Diagnostic delete test",
            )
            record = client.add_expense(expense_to_create)
            expense_key = record.key
            print(f"    Created expense key={expense_key}")
            
            create_state = capture_sync_state(db_path)
            print_sync_state(f"AFTER CREATE (expense {expense_key})", create_state)
            
            # Read test expense
            print(f"\n[2] Reading expense {expense_key}...")
            record = client.get_expense(expense_key)
            print(f"    Read successful: {record.amount} {record.account}")
            
            # Update test expense
            print(f"\n[3] Updating expense {expense_key}...")
            updated = client.update_expense(key=expense_key, amount=Decimal("30.00"))
            print(f"    Updated amount to {updated.amount}")
            
            update_state = capture_sync_state(db_path)
            print_sync_state(f"AFTER UPDATE (expense {expense_key})", update_state)
            
            # Delete test expense
            print(f"\n[4] Deleting expense {expense_key}...")
            client.delete_expense(expense_key)
            print(f"    Delete operation completed")
            
            delete_state = capture_sync_state(db_path)
            print_sync_state(f"AFTER DELETE (expense {expense_key})", delete_state)
            
            # Compare operations
            print("\n" + "="*80)
            print("OPERATION COMPARISON")
            print("="*80)
            
            all_states = {
                "Create": create_state,
                "Update": update_state,
                "Delete": delete_state,
            }
            
            for op_name, state in all_states.items():
                latest = state["syncs"][0] if state["syncs"] else {}
                op = latest.get("operation", "MISSING")
                updateType = latest.get("updateType", "MISSING")
                payload_len = latest.get("payload_len", "N/A")
                
                # Valid ranges from inspection: 683 (Delete/Income/Transfer), 832-920 (Expense)
                is_valid = payload_len in range(680, 925) if isinstance(payload_len, int) else False
                status = "✓" if is_valid else "⚠" if payload_len else "✗"
                print(f"{status} {op_name:10} Operation={op:20} Type={updateType:20} Len={payload_len}")
            
            print("\n✓ Diagnostic test completed")
            
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diagnostic test for delete operation sync"
    )
    parser.add_argument(
        "--db",
        type=Path,
        help="Path to HomeBudget database",
    )
    args = parser.parse_args()
    run_diagnostic(args.db)


if __name__ == "__main__":
    main()
