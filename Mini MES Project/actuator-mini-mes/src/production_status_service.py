from __future__ import annotations

import pandas as pd

from src.db import get_connection


def get_production_status() -> pd.DataFrame:
    """작업지시별 생산 진행 현황을 조회한다."""

    sql = """
        SELECT
            wo.work_order_id,
            wo.work_order_no,
            product.item_code,
            product.item_name,
            wo.planned_qty,

            COUNT(ps.product_serial_id) AS issued_qty,

            SUM(
                CASE
                    WHEN ps.status = 'CREATED' THEN 1
                    ELSE 0
                END
            ) AS created_qty,

            SUM(
                CASE
                    WHEN ps.status = 'IN_PROGRESS' THEN 1
                    ELSE 0
                END
            ) AS in_progress_qty,

            SUM(
                CASE
                    WHEN ps.status = 'PASS' THEN 1
                    ELSE 0
                END
            ) AS pass_qty,

            SUM(
                CASE
                    WHEN ps.status = 'FAIL' THEN 1
                    ELSE 0
                END
            ) AS fail_qty,

            SUM(
                CASE
                    WHEN ps.status IN ('PASS', 'FAIL') THEN 1
                    ELSE 0
                END
            ) AS finished_qty,

            ROUND(
                100.0 * SUM(
                    CASE
                        WHEN ps.status IN ('PASS', 'FAIL') THEN 1
                        ELSE 0
                    END
                ) / wo.planned_qty,
                1
            ) AS progress_rate,

            wo.status,
            wo.due_date,
            wo.started_at,
            wo.completed_at

        FROM work_order AS wo

        JOIN item AS product
          ON product.item_id = wo.product_item_id

        LEFT JOIN product_serial AS ps
          ON ps.work_order_id = wo.work_order_id

        GROUP BY
            wo.work_order_id,
            wo.work_order_no,
            product.item_code,
            product.item_name,
            wo.planned_qty,
            wo.status,
            wo.due_date,
            wo.started_at,
            wo.completed_at

        ORDER BY
            wo.created_at DESC,
            wo.work_order_no DESC
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def get_serial_status(work_order_id: int) -> pd.DataFrame:
    """선택한 작업지시에 속한 Serial별 생산 진행 상태를 조회한다."""

    sql = """
        SELECT
            ps.product_serial_id,
            ps.serial_no,
            ps.status,
            ps.started_at,
            ps.completed_at,

            (
                SELECT COUNT(*)
                FROM routing_step AS total_rs
                WHERE total_rs.product_item_id = wo.product_item_id
                  AND total_rs.is_required = 1
                  AND total_rs.is_active = 1
            ) AS total_process_qty,

            (
                SELECT COUNT(*)
                FROM process_history AS completed_ph
                JOIN routing_step AS completed_rs
                  ON completed_rs.routing_step_id =
                     completed_ph.routing_step_id
                WHERE completed_ph.product_serial_id =
                      ps.product_serial_id
                  AND completed_ph.result = 'PASS'
                  AND completed_rs.is_required = 1
                  AND completed_rs.is_active = 1
            ) AS completed_process_qty,

            (
                SELECT last_process.process_code
                FROM process_history AS last_ph
                JOIN routing_step AS last_rs
                  ON last_rs.routing_step_id =
                     last_ph.routing_step_id
                JOIN process AS last_process
                  ON last_process.process_id =
                     last_rs.process_id
                WHERE last_ph.product_serial_id =
                      ps.product_serial_id
                  AND last_ph.result = 'PASS'
                ORDER BY
                    last_ph.completed_at DESC,
                    last_rs.sequence_no DESC
                LIMIT 1
            ) AS last_process_code,

            (
                SELECT last_process.process_name
                FROM process_history AS last_ph
                JOIN routing_step AS last_rs
                  ON last_rs.routing_step_id =
                     last_ph.routing_step_id
                JOIN process AS last_process
                  ON last_process.process_id =
                     last_rs.process_id
                WHERE last_ph.product_serial_id =
                      ps.product_serial_id
                  AND last_ph.result = 'PASS'
                ORDER BY
                    last_ph.completed_at DESC,
                    last_rs.sequence_no DESC
                LIMIT 1
            ) AS last_process_name,

            (
                SELECT MAX(last_ph.completed_at)
                FROM process_history AS last_ph
                WHERE last_ph.product_serial_id =
                      ps.product_serial_id
                  AND last_ph.result = 'PASS'
            ) AS last_process_completed_at,

            CASE
                WHEN ps.status IN ('PASS', 'FAIL') THEN NULL
                ELSE (
                    SELECT next_process.process_code
                    FROM routing_step AS next_rs
                    JOIN process AS next_process
                      ON next_process.process_id =
                         next_rs.process_id
                    WHERE next_rs.product_item_id =
                          wo.product_item_id
                      AND next_rs.is_required = 1
                      AND next_rs.is_active = 1
                      AND NOT EXISTS (
                          SELECT 1
                          FROM process_history AS next_ph
                          WHERE next_ph.product_serial_id =
                                ps.product_serial_id
                            AND next_ph.routing_step_id =
                                next_rs.routing_step_id
                            AND next_ph.result = 'PASS'
                      )
                    ORDER BY next_rs.sequence_no
                    LIMIT 1
                )
            END AS next_process_code,

            CASE
                WHEN ps.status IN ('PASS', 'FAIL') THEN NULL
                ELSE (
                    SELECT next_process.process_name
                    FROM routing_step AS next_rs
                    JOIN process AS next_process
                      ON next_process.process_id =
                         next_rs.process_id
                    WHERE next_rs.product_item_id =
                          wo.product_item_id
                      AND next_rs.is_required = 1
                      AND next_rs.is_active = 1
                      AND NOT EXISTS (
                          SELECT 1
                          FROM process_history AS next_ph
                          WHERE next_ph.product_serial_id =
                                ps.product_serial_id
                            AND next_ph.routing_step_id =
                                next_rs.routing_step_id
                            AND next_ph.result = 'PASS'
                      )
                    ORDER BY next_rs.sequence_no
                    LIMIT 1
                )
            END AS next_process_name

        FROM product_serial AS ps

        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id

        WHERE ps.work_order_id = ?

        ORDER BY ps.serial_no
    """

    with get_connection() as connection:
        dataframe = pd.read_sql_query(
            sql,
            connection,
            params=(work_order_id,),
        )

    if not dataframe.empty:
        dataframe["process_progress_rate"] = (
            100.0
            * dataframe["completed_process_qty"]
            / dataframe["total_process_qty"]
        ).round(1)

    return dataframe

def get_serial_process_status(
    product_serial_id: int,
) -> pd.DataFrame:
    """Serial의 라우팅 공정별 진행 상태를 조회한다."""

    sql = """
        SELECT
            rs.routing_step_id,
            rs.sequence_no,
            p.process_code,
            p.process_name,
            p.process_type,
            rs.is_required,

            ph.process_history_id,
            ph.result,
            ph.started_at,
            ph.completed_at,
            ph.remark,

            CASE
                WHEN ph.process_history_id IS NULL
                    THEN 'NOT_STARTED'

                WHEN ph.completed_at IS NULL
                    THEN 'IN_PROGRESS'

                WHEN ph.result = 'PASS'
                    THEN 'PASS'

                WHEN ph.result = 'FAIL'
                    THEN 'FAIL'

                ELSE 'IN_PROGRESS'
            END AS process_status

        FROM product_serial AS ps

        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id

        JOIN routing_step AS rs
          ON rs.product_item_id = wo.product_item_id
         AND rs.is_active = 1

        JOIN process AS p
          ON p.process_id = rs.process_id

        LEFT JOIN process_history AS ph
          ON ph.product_serial_id = ps.product_serial_id
         AND ph.routing_step_id = rs.routing_step_id

        WHERE ps.product_serial_id = ?

        ORDER BY rs.sequence_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(product_serial_id,),
        )
