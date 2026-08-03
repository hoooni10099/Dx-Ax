from __future__ import annotations

import pandas as pd

from src.db import get_connection


def get_work_order_progress() -> pd.DataFrame:
    """작업지시별 계획수량과 생산 완료수량을 조회한다."""

    sql = """
        SELECT
            wo.work_order_no,
            i.item_name,
            wo.planned_qty,
            COUNT(
                CASE
                    WHEN ps.status IN ('PASS', 'FAIL')
                    THEN 1
                END
            ) AS completed_qty
        FROM work_order AS wo
        JOIN item AS i
          ON i.item_id = wo.product_item_id
        LEFT JOIN product_serial AS ps
          ON ps.work_order_id = wo.work_order_id
        WHERE wo.status <> 'CANCELLED'
        GROUP BY
            wo.work_order_id,
            wo.work_order_no,
            i.item_name,
            wo.planned_qty
        ORDER BY wo.created_at DESC
        LIMIT 10
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def get_current_process_counts() -> pd.DataFrame:
    """미완료 Serial이 다음으로 수행할 공정별 대기 수량을 조회한다."""

    sql = """
        WITH serial_next_process AS (
            SELECT
                ps.product_serial_id,
                (
                    SELECT rs.routing_step_id
                    FROM routing_step AS rs
                    WHERE rs.product_item_id = wo.product_item_id
                      AND rs.is_active = 1
                      AND rs.is_required = 1
                      AND NOT EXISTS (
                          SELECT 1
                          FROM process_history AS ph
                          WHERE ph.product_serial_id =
                                ps.product_serial_id
                            AND ph.routing_step_id =
                                rs.routing_step_id
                      )
                    ORDER BY rs.sequence_no
                    LIMIT 1
                ) AS next_routing_step_id
            FROM product_serial AS ps
            JOIN work_order AS wo
              ON wo.work_order_id = ps.work_order_id
            WHERE ps.status IN ('CREATED', 'IN_PROGRESS')
              AND wo.status IN ('PLANNED', 'IN_PROGRESS')
        )
        SELECT
            p.process_name,
            rs.sequence_no,
            COUNT(*) AS product_qty
        FROM serial_next_process AS snp
        JOIN routing_step AS rs
          ON rs.routing_step_id = snp.next_routing_step_id
        JOIN process AS p
          ON p.process_id = rs.process_id
        GROUP BY
            p.process_id,
            p.process_name,
            rs.sequence_no
        ORDER BY rs.sequence_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def get_daily_production(days: int = 7) -> pd.DataFrame:
    """오늘을 포함한 최근 일자별 생산 완료수량을 조회한다."""

    sql = """
        WITH RECURSIVE dates(production_date) AS (
            SELECT date('now', 'localtime', ?)

            UNION ALL

            SELECT date(production_date, '+1 day')
            FROM dates
            WHERE production_date < date('now', 'localtime')
        ),
        daily_count AS (
            SELECT
                date(completed_at) AS production_date,
                COUNT(*) AS production_qty
            FROM product_serial
            WHERE status IN ('PASS', 'FAIL')
              AND completed_at IS NOT NULL
              AND date(completed_at)
                  >= date('now', 'localtime', ?)
            GROUP BY date(completed_at)
        )
        SELECT
            dates.production_date,
            COALESCE(daily_count.production_qty, 0)
                AS production_qty
        FROM dates
        LEFT JOIN daily_count
          ON daily_count.production_date =
             dates.production_date
        ORDER BY dates.production_date
    """

    start_modifier = f"-{days - 1} days"

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(start_modifier, start_modifier),
        )

def get_quality_result_counts() -> pd.DataFrame:
    """최종 생산완료 제품의 합격·불합격 수량을 조회한다."""

    sql = """
        SELECT
            CASE status
                WHEN 'PASS' THEN '합격'
                WHEN 'FAIL' THEN '불합격'
            END AS result_name,
            COUNT(*) AS result_qty
        FROM product_serial
        WHERE status IN ('PASS', 'FAIL')
        GROUP BY status
        ORDER BY
            CASE status
                WHEN 'PASS' THEN 1
                WHEN 'FAIL' THEN 2
            END
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

