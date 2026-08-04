from __future__ import annotations

import pandas as pd

from src.db import get_connection


def get_eol_current_trend(
    product_item_id: int | None = None,
    work_order_id: int | None = None,
) -> pd.DataFrame:
    """EOL 검사별 최대전류 추이 데이터를 조회한다."""

    sql = """
        SELECT
            etr.eol_test_result_id,
            etr.tested_at,
            etr.max_current_ma,
            etr.result,
            ps.serial_no,
            wo.work_order_id,
            wo.work_order_no,
            product.item_id AS product_item_id,
            product.item_code AS product_code,
            product.item_name AS product_name
        FROM eol_test_result AS etr
        JOIN process_history AS ph
          ON ph.process_history_id = etr.process_history_id
        JOIN product_serial AS ps
          ON ps.product_serial_id = ph.product_serial_id
        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id
        JOIN item AS product
          ON product.item_id = wo.product_item_id
        WHERE (? IS NULL OR product.item_id = ?)
          AND (? IS NULL OR wo.work_order_id = ?)
        ORDER BY
            etr.tested_at,
            etr.eol_test_result_id
    """

    params = (
        product_item_id,
        product_item_id,
        work_order_id,
        work_order_id,
    )

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )

def get_eol_operation_time_distribution(
    product_item_id: int | None = None,
    work_order_id: int | None = None,
) -> pd.DataFrame:
    """EOL 검사의 정·역방향 동작시간 데이터를 조회한다."""

    sql = """
        SELECT
            etr.eol_test_result_id,
            etr.tested_at,
            etr.forward_time_ms,
            etr.reverse_time_ms,
            etr.result,
            ps.serial_no,
            wo.work_order_id,
            wo.work_order_no,
            product.item_id AS product_item_id,
            product.item_code AS product_code,
            product.item_name AS product_name
        FROM eol_test_result AS etr
        JOIN process_history AS ph
          ON ph.process_history_id = etr.process_history_id
        JOIN product_serial AS ps
          ON ps.product_serial_id = ph.product_serial_id
        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id
        JOIN item AS product
          ON product.item_id = wo.product_item_id
        WHERE (? IS NULL OR product.item_id = ?)
          AND (? IS NULL OR wo.work_order_id = ?)
        ORDER BY
            etr.tested_at,
            etr.eol_test_result_id
    """

    params = (
        product_item_id,
        product_item_id,
        work_order_id,
        work_order_id,
    )

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )

def get_eol_result_summary(
    product_item_id: int | None = None,
    work_order_id: int | None = None,
) -> pd.DataFrame:
    """제품·작업지시별 EOL 검사 결과를 집계한다."""

    sql = """
        SELECT
            COUNT(*) AS total_count,

            SUM(
                CASE
                    WHEN etr.result = 'PASS' THEN 1
                    ELSE 0
                END
            ) AS pass_count,

            SUM(
                CASE
                    WHEN etr.result = 'FAIL' THEN 1
                    ELSE 0
                END
            ) AS fail_count

        FROM eol_test_result AS etr

        JOIN process_history AS ph
          ON ph.process_history_id = etr.process_history_id

        JOIN product_serial AS ps
          ON ps.product_serial_id = ph.product_serial_id

        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id

        WHERE (? IS NULL OR wo.product_item_id = ?)
          AND (? IS NULL OR wo.work_order_id = ?)
    """

    params = (
        product_item_id,
        product_item_id,
        work_order_id,
        work_order_id,
    )

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )

