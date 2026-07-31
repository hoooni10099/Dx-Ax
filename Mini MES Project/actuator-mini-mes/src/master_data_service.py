from __future__ import annotations

import pandas as pd

from src.db import get_connection


def get_items(
    item_type: str | None = None,
    is_active: int | None = None,
    keyword: str | None = None,
) -> pd.DataFrame:
    sql = """
        SELECT
            item_code AS "품목코드",
            item_name AS "품목명",
            item_type AS "품목유형",
            CASE is_active
                WHEN 1 THEN '사용'
                ELSE '미사용'
            END AS "사용여부"
        FROM item
        WHERE 1 = 1
    """

    params = []

    if item_type is not None:
        sql += """
            AND item_type = ?
        """
        params.append(item_type)

    if is_active is not None:
        sql += """
            AND is_active = ?
        """
        params.append(is_active)

    if keyword is not None and keyword.strip():
        sql += """
            AND (
                item_code LIKE ?
                OR item_name LIKE ?
            )
        """

        search_keyword = f"%{keyword.strip()}%"
        params.extend([search_keyword, search_keyword])

    sql += """
        ORDER BY
            CASE item_type
                WHEN 'PRODUCT' THEN 1
                WHEN 'MATERIAL' THEN 2
                ELSE 3
            END,
            item_code
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )
