#!/usr/bin/env python
"""Utility script to find and delete transfers matching criteria for UAT cleanup."""

from __future__ import annotations

import argparse
import datetime as dt
from decimal import Decimal
from pathlib import Path

from homebudget.client import HomeBudgetClient
from homebudget.models import TransferDTO


def main() -> None:
    """Find and delete transfers matching criteria."""
    parser = argparse.ArgumentParser(
        description="Find and delete transfers matching criteria"
    )
    parser.add_argument("--date", required=True, help="Transfer date (YYYY-MM-DD)")
    parser.add_argument("--from-account", required=True, help="From account name")
    parser.add_argument("--to-account", required=True, help="To account name")
    parser.add_argument("--amount", required=False, help="Amount to match")
    parser.add_argument("--db", default="config/hb.db", help="Database path")
    
    args = parser.parse_args()
    
    try:
        transfer_date = dt.datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError as e:
        print(f"Invalid date format: {e}")
        return
    
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
    
    with HomeBudgetClient(db_path=db_path, enable_sync=False) as client:
        # List all transfers for the date
        transfers = client.list_transfers(start_date=transfer_date, end_date=transfer_date)
        
        # Filter by criteria
        matches = []
        for transfer in transfers:
            if (transfer.date == transfer_date and
                transfer.from_account == args.from_account and
                transfer.to_account == args.to_account):
                
                if args.amount:
                    try:
                        target_amount = Decimal(args.amount)
                        if transfer.amount == target_amount:
                            matches.append(transfer)
                    except ValueError:
                        print(f"Invalid amount: {args.amount}")
                        return
                else:
                    matches.append(transfer)
        
        if not matches:
            print(f"No transfers found matching criteria")
            return
        
        print(f"Found {len(matches)} transfer(s) matching criteria:")
        for t in matches:
            print(f"  {t.key}: {t.date} {t.from_account} → {t.to_account} {t.amount}")
        
        # Delete all matches
        print(f"\nDeleting {len(matches)} transfer(s)...")
        for transfer in matches:
            try:
                client.delete_transfer(transfer.key)
                print(f"  Deleted: {transfer.key}")
            except Exception as e:
                print(f"  Error deleting {transfer.key}: {e}")
        
        print("Cleanup complete")


if __name__ == "__main__":
    main()
