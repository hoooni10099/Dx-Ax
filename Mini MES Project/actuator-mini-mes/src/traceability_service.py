from __future__ import annotations

import pandas as pd

from src.db import get_connection


def get_serial_options() -> pd.DataFrame:
    """추적 조회에 사용할 전체 Serial 목록을 조회한다."""

    sql = """
        SELECT
            ps.product_serial_id,
            ps.serial_no,
            ps.status,
            wo.work_order_no,
            i.item_code,
            i.item_name

        FROM product_serial AS ps

        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id

        JOIN item AS i
          ON i.item_id = wo.product_item_id

        ORDER BY ps.serial_no DESC
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def get_serial_summary(
    product_serial_id: int,
) -> pd.DataFrame:
    """Serial의 제품 및 작업지시 기본 정보를 조회한다."""

    sql = """
        SELECT
            ps.product_serial_id,
            ps.serial_no,
            ps.status AS serial_status,
            ps.started_at AS serial_started_at,
            ps.completed_at AS serial_completed_at,

            wo.work_order_id,
            wo.work_order_no,
            wo.status AS work_order_status,
            wo.planned_qty,
            wo.due_date,

            i.item_code,
            i.item_name

        FROM product_serial AS ps

        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id

        JOIN item AS i
          ON i.item_id = wo.product_item_id

        WHERE ps.product_serial_id = ?
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(product_serial_id,),
        )

def get_serial_material_trace(
    product_serial_id: int,
) -> pd.DataFrame:
    """Serial 생산에 실제 투입된 자재 LOT를 조회한다."""

    sql = """
        SELECT
            mc.consumption_id,

            material.item_code AS material_code,
            material.item_name AS material_name,

            ml.lot_no,
            ml.received_date,
            ml.status AS lot_status,

            mc.consumed_qty,
            mc.consumed_at,

            rs.sequence_no,
            p.process_code,
            p.process_name

        FROM material_consumption AS mc

        JOIN material_lot AS ml
          ON ml.material_lot_id = mc.material_lot_id

        JOIN item AS material
          ON material.item_id = ml.material_item_id

        JOIN routing_step AS rs
          ON rs.routing_step_id = mc.routing_step_id

        JOIN process AS p
          ON p.process_id = rs.process_id

        WHERE mc.product_serial_id = ?

        ORDER BY
            rs.sequence_no,
            material.item_code,
            ml.lot_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(product_serial_id,),
        )

def get_serial_process_history(
    product_serial_id: int,
) -> pd.DataFrame:
    """Serial의 공정별 작업 이력을 조회한다."""

    sql = """
        SELECT
            ph.process_history_id,

            rs.sequence_no,
            rs.is_required,

            p.process_code,
            p.process_name,
            p.process_type,

            ph.result,
            ph.started_at,
            ph.completed_at,
            ph.remark

        FROM process_history AS ph

        JOIN routing_step AS rs
          ON rs.routing_step_id = ph.routing_step_id

        JOIN process AS p
          ON p.process_id = rs.process_id

        WHERE ph.product_serial_id = ?

        ORDER BY rs.sequence_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(product_serial_id,),
        )

def get_serial_eol_result(
    product_serial_id: int,
) -> pd.DataFrame:
    """Serial의 EOL 성능 검사 결과를 조회한다."""

    sql = """
        SELECT
            eol.eol_test_result_id,

            p.process_code,
            p.process_name,

            eol.forward_ok,
            eol.reverse_ok,
            eol.forward_time_ms,
            eol.reverse_time_ms,
            eol.max_current_ma,

            eol.target_angle_deg,
            eol.actual_angle_deg,
            eol.position_error_deg,

            eol.result,
            eol.failure_reason,
            eol.tested_at

        FROM eol_test_result AS eol

        JOIN process_history AS ph
          ON ph.process_history_id = eol.process_history_id

        JOIN routing_step AS rs
          ON rs.routing_step_id = ph.routing_step_id

        JOIN process AS p
          ON p.process_id = rs.process_id

        WHERE ph.product_serial_id = ?

        ORDER BY eol.tested_at DESC
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(product_serial_id,),
        )

def get_material_lot_options() -> pd.DataFrame:
    """역방향 추적 화면에서 선택할 자재 LOT 목록을 조회한다."""

    sql = """
        SELECT
            ml.material_lot_id,
            ml.lot_no,
            i.item_code AS material_code,
            i.item_name AS material_name,
            ml.status AS lot_status

        FROM material_lot AS ml

        JOIN item AS i
          ON i.item_id = ml.material_item_id

        ORDER BY ml.received_date DESC, ml.lot_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
        )

def get_material_lot_summary(
    material_lot_id: int,
) -> pd.DataFrame:
    """선택한 자재 LOT의 기본정보와 누적 투입 수량을 조회한다."""

    sql = """
        SELECT
            ml.material_lot_id,
            ml.lot_no,
            ml.received_qty,
            ml.received_date,
            ml.status AS lot_status,
            ml.created_at,

            i.item_code AS material_code,
            i.item_name AS material_name,

            COALESCE(
                SUM(mc.consumed_qty),
                0
            ) AS consumed_qty,

            ml.received_qty
            - COALESCE(
                SUM(mc.consumed_qty),
                0
            ) AS remaining_qty

        FROM material_lot AS ml

        JOIN item AS i
          ON i.item_id = ml.material_item_id

        LEFT JOIN material_consumption AS mc
          ON mc.material_lot_id = ml.material_lot_id

        WHERE ml.material_lot_id = ?

        GROUP BY
            ml.material_lot_id,
            ml.lot_no,
            ml.received_qty,
            ml.received_date,
            ml.status,
            ml.created_at,
            i.item_code,
            i.item_name
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(material_lot_id,),
        )

def get_lot_serial_trace(
    material_lot_id: int,
) -> pd.DataFrame:
    """선택한 자재 LOT가 투입된 완제품 Serial을 조회한다."""

    sql = """
        SELECT
            mc.consumption_id,
            mc.consumed_qty,
            mc.consumed_at,

            ps.product_serial_id,
            ps.serial_no,
            ps.status AS serial_status,

            wo.work_order_no,
            wo.status AS work_order_status,

            product.item_code AS product_code,
            product.item_name AS product_name,

            rs.sequence_no,
            p.process_code,
            p.process_name

        FROM material_consumption AS mc

        JOIN product_serial AS ps
          ON ps.product_serial_id = mc.product_serial_id

        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id

        JOIN item AS product
          ON product.item_id = wo.product_item_id

        JOIN routing_step AS rs
          ON rs.routing_step_id = mc.routing_step_id

        JOIN process AS p
          ON p.process_id = rs.process_id

        WHERE mc.material_lot_id = ?

        ORDER BY
            mc.consumed_at DESC,
            ps.serial_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(material_lot_id,),
        )

