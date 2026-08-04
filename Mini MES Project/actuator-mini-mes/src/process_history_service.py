from __future__ import annotations

import pandas as pd

from src.db import get_connection


def get_process_performance_metrics() -> dict:
    """공정실적 페이지 상단 핵심 지표를 조회한다."""

    sql = """
        WITH expected_process AS (
            SELECT
                ps.product_serial_id,
                rs.routing_step_id
            FROM product_serial AS ps
            JOIN work_order AS wo
              ON wo.work_order_id = ps.work_order_id
            JOIN routing_step AS rs
              ON rs.product_item_id = wo.product_item_id
             AND rs.is_active = 1
             AND rs.is_required = 1
        ),
        required_performance AS (
            SELECT
                ep.product_serial_id,
                ep.routing_step_id,
                ph.result,
                ph.completed_at
            FROM expected_process AS ep
            LEFT JOIN process_history AS ph
              ON ph.product_serial_id = ep.product_serial_id
             AND ph.routing_step_id = ep.routing_step_id
        ),
        history_counts AS (
            SELECT
                COUNT(*) AS total_history_count,
                SUM(
                    CASE WHEN result = 'PASS' THEN 1 ELSE 0 END
                ) AS pass_count,
                SUM(
                    CASE WHEN result = 'FAIL' THEN 1 ELSE 0 END
                ) AS fail_count
            FROM process_history
        ),
        completion_counts AS (
            SELECT
                COUNT(*) AS expected_process_count,
                SUM(
                    CASE
                        WHEN completed_at IS NOT NULL
                         AND result IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS completed_process_count
            FROM required_performance
        )
        SELECT
            hc.total_history_count,
            hc.pass_count,
            hc.fail_count,
            cc.expected_process_count,
            cc.completed_process_count
        FROM history_counts AS hc
        CROSS JOIN completion_counts AS cc
    """

    with get_connection() as connection:
        row = connection.execute(sql).fetchone()

    expected_count = int(row["expected_process_count"] or 0)
    completed_count = int(row["completed_process_count"] or 0)

    completion_rate = (
        completed_count / expected_count * 100
        if expected_count > 0
        else 0.0
    )

    return {
        "total_history_count": int(row["total_history_count"] or 0),
        "pass_count": int(row["pass_count"] or 0),
        "fail_count": int(row["fail_count"] or 0),
        "expected_process_count": expected_count,
        "completed_process_count": completed_count,
        "completion_rate": completion_rate,
    }

def get_process_result_summary() -> pd.DataFrame:
    """공정별 합격·불합격 실적 수량을 조회한다."""

    sql = """
        WITH active_process AS (
            SELECT
                p.process_id,
                p.process_code,
                p.process_name,
                MIN(rs.sequence_no) AS sequence_no
            FROM process AS p
            JOIN routing_step AS rs
              ON rs.process_id = p.process_id
             AND rs.is_active = 1
            GROUP BY
                p.process_id,
                p.process_code,
                p.process_name
        ),
        result_type AS (
            SELECT 'PASS' AS result
            UNION ALL
            SELECT 'FAIL'
        ),
        process_result_count AS (
            SELECT
                rs.process_id,
                ph.result,
                COUNT(*) AS result_qty
            FROM process_history AS ph
            JOIN routing_step AS rs
              ON rs.routing_step_id = ph.routing_step_id
            WHERE ph.result IN ('PASS', 'FAIL')
            GROUP BY
                rs.process_id,
                ph.result
        )
        SELECT
            ap.process_code,
            ap.process_name,
            ap.sequence_no,
            rt.result,
            CASE rt.result
                WHEN 'PASS' THEN '합격'
                WHEN 'FAIL' THEN '불합격'
            END AS result_name,
            COALESCE(prc.result_qty, 0) AS result_qty
        FROM active_process AS ap
        CROSS JOIN result_type AS rt
        LEFT JOIN process_result_count AS prc
          ON prc.process_id = ap.process_id
         AND prc.result = rt.result
        ORDER BY
            ap.sequence_no,
            CASE rt.result
                WHEN 'PASS' THEN 1
                WHEN 'FAIL' THEN 2
            END
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

