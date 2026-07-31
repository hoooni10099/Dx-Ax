from __future__ import annotations

import pandas as pd

from src.db import get_connection

# 02_자재_LOT_관리.py

def get_materials() -> pd.DataFrame:
    sql = """
        SELECT
            item_id,
            item_code,
            item_name
        FROM item
        WHERE item_type = 'MATERIAL'
          AND is_active = 1
        ORDER BY item_code
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)
