from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3


def copy_fixture_to(tmp_path: Path, fixture_path: Path) -> Path:
    target = tmp_path / fixture_path.name
    shutil.copyfile(fixture_path, target)
    return target


def open_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection
