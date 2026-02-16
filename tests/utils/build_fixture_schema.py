#!/usr/bin/env python
"""Build schema JSON and schema only fixture database.

Run this script with .dev env to create test resources.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3


def load_schema_statements(source_db: Path) -> list[dict[str, str]]:
    with sqlite3.connect(source_db) as source:
        rows = source.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE sql IS NOT NULL
              AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        ).fetchall()
    return [{"type": row[0], "name": row[1], "sql": row[2]} for row in rows if row[2]]


def write_schema_json(schema_path: Path, statements: list[dict[str, str]]) -> None:
    payload = {"statements": statements}
    with schema_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def build_schema_only_db(schema_path: Path, target_db: Path) -> None:
    with schema_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    statements = payload.get("statements", [])
    priority = {"table": 0, "index": 1, "trigger": 2, "view": 3}
    ordered = sorted(
        statements,
        key=lambda item: (priority.get(item.get("type", ""), 99), item.get("name", "")),
    )
    with sqlite3.connect(target_db) as target:
        for item in ordered:
            target.execute(item["sql"])
        target.commit()


def main() -> None:
    workspace = Path(__file__).resolve().parents[2]
    source_db = workspace / "reference" / "hb-sqlite-db" / "homebudget.db"
    schema_path = workspace / "tests" / "schema.json"
    target_db = workspace / "tests" / "fixtures" / "empty_database.db"

    statements = load_schema_statements(source_db)
    write_schema_json(schema_path, statements)

    if target_db.exists():
        target_db.unlink()
    build_schema_only_db(schema_path, target_db)

    print(f"Wrote schema JSON to {schema_path}")
    print(f"Created schema only database at {target_db}")


if __name__ == "__main__":
    main()
