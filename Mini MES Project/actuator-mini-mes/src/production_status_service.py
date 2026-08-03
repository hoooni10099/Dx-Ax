from __future__ import annotations

import pandas as pd

from src.db import get_connection


def get_production_status() -> pd.DataFrame:
    """작업지시별 생산 진행 현황을 조회한다."""

    sql = """
        -- 다음 단계에서 작업지시별 집계 SQL 작성
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)
