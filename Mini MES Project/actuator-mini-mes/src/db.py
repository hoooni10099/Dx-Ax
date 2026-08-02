from pathlib import Path
import sqlite3

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "sql" / "mes_dev.db"

def database_exists() -> bool:
    return DB_PATH.exists()

def get_connection() -> sqlite3.Connection:
    if not database_exists():
        raise FileNotFoundError(f"SQLite 데이터베이스 파일을 찾을 수 없습니다 : {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def test_connection() -> dict:
    with get_connection() as connection:
        foreign_keys = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        table_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchone()[0]

        integrity_check = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

    return {
        "database_path": str(DB_PATH),
        "foreign_keys": foreign_keys,
        "table_count": table_count,
        "integrity_check": integrity_check,
    }
