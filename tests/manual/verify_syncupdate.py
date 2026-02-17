#!/usr/bin/env python
"""Verify the latest SyncUpdate entry exists and report its details."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import sqlite3
from typing import Any
import zlib

# SyncUpdate payload decoding constant (must match encoder in sync.py)
ZLIB_WBITS = 15  # Full zlib format with header and checksum


@dataclass(frozen=True)
class SyncUpdateRecord:
    key: int
    payload: dict[str, Any]


class SyncUpdateVerifier:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def fetch_latest_raw(self) -> tuple[int, str] | None:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            row = connection.execute(
                "SELECT key, payload FROM SyncUpdate ORDER BY key DESC LIMIT 1"
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        return int(row["key"]), str(row["payload"])


def _decode_sync_payload(payload: str) -> dict[str, Any]:
    """Decode HomeBudget SyncUpdate payload to operation dictionary.
    
    HomeBudget encodes payloads with the following process:
    1. JSON serialize operation data
    2. Compress with full zlib format (includes header and checksum)
    3. Pad to 660 bytes with null bytes
    4. Encode with URL-safe base64 (- and _ instead of + and /)
    5. Strip trailing = padding
    
    This function reverses that process to extract the operation data.
    
    Critical discoveries (2026-02-17):
    - Native app uses FULL zlib format with header, NOT raw deflate
    - Decompression requires wbits=15 (full format), not wbits=-15 (raw)
    - URL-safe base64: - maps to +, _ maps to /
    - All payloads padded to 660 bytes before encoding (880 chars after)
    
    Args:
        payload: 880-character URL-safe base64 encoded string from SyncUpdate.payload
        
    Returns:
        Dictionary containing decoded operation (e.g., AddExpense payload)
        
    Raises:
        ValueError: If decoding or decompression fails
    """
    cleaned = payload.strip()
    
    # HomeBudget uses URL-safe base64: convert - to + and _ to /
    cleaned = cleaned.replace('-', '+').replace('_', '/')
    
    # Add padding if needed for base64
    if len(cleaned) % 4 != 0:
        padding = '=' * (-len(cleaned) % 4)
        cleaned = cleaned + padding
    
    # Decode base64 first - this gives us the raw bytes
    try:
        raw = base64.b64decode(cleaned)
    except binascii.Error as exc:
        raise ValueError(f"Base64 decode failed: {exc}") from exc
    
    # NOW strip trailing null bytes from the binary data
    # HomeBudget app pads compressed data to 660 bytes with 0x00
    raw = raw.rstrip(b'\x00')
    
    # Decompress using full zlib format (inverse of encoding with zlib.compress())
    # NOTE: Initial implementation incorrectly used wbits=-15 (raw deflate)
    try:
        inflated = zlib.decompress(raw, wbits=ZLIB_WBITS)
    except zlib.error as exc:
        raise ValueError(f"Zlib decompress failed: {exc}") from exc
    
    # Parse JSON
    try:
        decoded = json.loads(inflated.decode("utf-8"))
        return decoded
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"JSON decode failed: {exc}") from exc


def _resolve_config_path(config_path: str | None) -> Path:
    if config_path:
        return Path(config_path)
    base_dir = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not base_dir:
        raise ValueError("USERPROFILE is not set and no --config was provided")
    return Path(base_dir) / "OneDrive" / "Documents" / "HomeBudgetData" / "hb-config.json"


def _resolve_db_path(db_path: str | None, config_path: str | None) -> Path:
    if db_path:
        return Path(db_path)
    resolved_config = _resolve_config_path(config_path)
    if not resolved_config.exists():
        raise ValueError("hb-config.json not found, pass --db or --config")
    with resolved_config.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    resolved_db = payload.get("db_path")
    if not resolved_db:
        raise ValueError("db_path is missing in hb-config.json")
    return Path(resolved_db)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify latest SyncUpdate entry.")
    parser.add_argument("--db", type=str, help="Path to HomeBudget database.")
    parser.add_argument("--config", type=str, help="Path to hb-config.json.")
    parser.add_argument(
        "--min-key",
        type=int,
        help="Fail if the latest SyncUpdate key is not greater than this value.",
    )
    parser.add_argument(
        "--print-payload",
        action="store_true",
        help="Print the decoded payload JSON.",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Write the decoded payload JSON to a file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = _resolve_db_path(args.db, args.config)
    verifier = SyncUpdateVerifier(db_path)
    latest_raw = verifier.fetch_latest_raw()
    if latest_raw is None:
        print("No SyncUpdate entries found.")
        return 1
    latest_key, raw_payload = latest_raw
    if args.min_key is not None and latest_key <= args.min_key:
        print(
            "Latest SyncUpdate key is not newer than expected. "
            f"Expected > {args.min_key}, got {latest_key}."
        )
        return 1
    try:
        decoded = _decode_sync_payload(raw_payload)
    except ValueError as exc:
        print(f"Failed to decode SyncUpdate payload: {exc}")
        print(f"Raw payload length: {len(raw_payload)}")
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as handle:
                handle.write(raw_payload)
                handle.write("\n")
            print(f"Wrote raw payload to {output_path}")
        return 1
    latest = SyncUpdateRecord(key=latest_key, payload=decoded)
    operation = latest.payload.get("Operation", "")
    expense_keys = latest.payload.get("expenseDeviceKeys", [])
    print(f"Latest SyncUpdate key: {latest.key}")
    print(f"Operation: {operation}")
    print(f"Expense keys: {expense_keys}")
    if args.print_payload:
        print("Payload:")
        print(json.dumps(latest.payload, indent=2, sort_keys=True))
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(latest.payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
