import sqlite3

from src.db import get_connection


def test_temporary_database_connection(test_db):
    """
    서비스가 원본 mes_dev.db가 아닌 임시 DB에 연결되는지 확인한다.
    """
    with get_connection() as connection:
        foreign_keys = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        integrity_result = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        item_count = connection.execute(
            "SELECT COUNT(*) FROM item"
        ).fetchone()[0]

    assert foreign_keys == 1
    assert integrity_result == "ok"
    assert item_count > 0


def test_original_database_is_not_modified(test_db):
    """
    임시 DB에 입력한 데이터가 원본 DB에 반영되지 않는지 확인한다.
    """
    test_item_code = "MAT-PYTEST-TEMP"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO item (
                item_code,
                item_name,
                item_type,
                is_active
            )
            VALUES (?, ?, 'MATERIAL', 1)
            """,
            (
                test_item_code,
                "pytest 임시 자재",
            ),
        )
        connection.commit()

    with sqlite3.connect(test_db) as connection:
        temporary_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM item
            WHERE item_code = ?
            """,
            (test_item_code,),
        ).fetchone()[0]

    assert temporary_count == 1
