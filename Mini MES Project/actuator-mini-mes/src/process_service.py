from __future__ import annotations

import pandas as pd
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from src.db import get_connection

EOL_MAX_OPERATION_TIME_MS = 1000
EOL_MAX_CURRENT_MA = 1500.0
EOL_MAX_POSITION_ERROR_DEG = 3.0

@dataclass
class ServiceResult:
    success: bool
    message: str

def get_process_ready_serials() -> pd.DataFrame:
    """다음 일반 공정을 등록할 수 있는 제품 Serial을 조회한다."""

    sql = """
        SELECT
            ps.product_serial_id,
            ps.serial_no,
            ps.status AS serial_status,
            wo.work_order_no,
            wo.work_order_id,
            i.item_code,
            i.item_name,
            rs.routing_step_id,
            rs.sequence_no,
            p.process_code,
            p.process_name,
            p.process_type
        FROM product_serial AS ps
        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id
        JOIN item AS i
          ON i.item_id = wo.product_item_id
        JOIN routing_step AS rs
          ON rs.product_item_id = wo.product_item_id
         AND rs.is_active = 1
         AND rs.is_required = 1
        JOIN process AS p
          ON p.process_id = rs.process_id
        WHERE ps.status IN ('CREATED', 'IN_PROGRESS')
          AND wo.status IN ('PLANNED', 'IN_PROGRESS')
          AND p.process_code NOT IN ('PROC-EOL', 'PROC-COMPLETE')
          AND rs.routing_step_id = (
              SELECT rs_next.routing_step_id
              FROM routing_step AS rs_next
              WHERE rs_next.product_item_id = wo.product_item_id
                AND rs_next.is_active = 1
                AND rs_next.is_required = 1
                AND NOT EXISTS (
                    SELECT 1
                    FROM process_history AS ph
                    WHERE ph.product_serial_id = ps.product_serial_id
                      AND ph.routing_step_id = rs_next.routing_step_id
                )
              ORDER BY rs_next.sequence_no
              LIMIT 1
          )
        ORDER BY
            ps.created_at,
            ps.product_serial_id
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def get_required_material_lots(
    product_serial_id: int,
    routing_step_id: int,
) -> pd.DataFrame:
    """선택한 Serial과 공정에 필요한 자재 및 사용 가능한 LOT를 조회한다."""

    sql = """
        WITH lot_balance AS (
            SELECT
                ml.material_lot_id,
                ml.lot_no,
                ml.material_item_id,
                ml.received_qty,
                ml.received_date,
                ml.status,
                ml.received_qty
                    - COALESCE(SUM(mc.consumed_qty), 0)
                    AS available_qty
            FROM material_lot AS ml
            LEFT JOIN material_consumption AS mc
              ON mc.material_lot_id = ml.material_lot_id
            GROUP BY
                ml.material_lot_id,
                ml.lot_no,
                ml.material_item_id,
                ml.received_qty,
                ml.received_date,
                ml.status
        )
        SELECT
            b.bom_id,
            b.material_item_id,
            material.item_code AS material_code,
            material.item_name AS material_name,
            b.required_qty,
            lb.material_lot_id,
            lb.lot_no,
            lb.received_date,
            lb.available_qty
        FROM product_serial AS ps
        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id
        JOIN bom AS b
          ON b.product_item_id = wo.product_item_id
         AND b.input_routing_step_id = ?
         AND b.is_active = 1
        JOIN item AS material
          ON material.item_id = b.material_item_id
        LEFT JOIN lot_balance AS lb
          ON lb.material_item_id = b.material_item_id
         AND lb.status = 'AVAILABLE'
         AND lb.available_qty >= b.required_qty
        WHERE ps.product_serial_id = ?
        ORDER BY
            material.item_code,
            lb.received_date,
            lb.material_lot_id
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(
                routing_step_id,
                product_serial_id,
            ),
        )

def register_process_result(
    product_serial_id: int,
    routing_step_id: int,
    selected_lot_ids: dict[int, int],
    result: str = "PASS",
    remark: str | None = None,
) -> ServiceResult:
    """공정 실적과 BOM 기준 자재 LOT 사용 이력을 함께 등록한다."""

    try:
        product_serial_id = int(product_serial_id)
        routing_step_id = int(routing_step_id)
        selected_lot_ids = {
            int(material_item_id): int(material_lot_id)
            for material_item_id, material_lot_id
            in selected_lot_ids.items()
        }
    except (TypeError, ValueError, AttributeError):
        return ServiceResult(
            success=False,
            message="Serial, 공정 또는 자재 LOT 선택값이 올바르지 않습니다.",
        )

    result = str(result).strip().upper()

    if result not in ("PASS", "FAIL"):
        return ServiceResult(
            success=False,
            message="공정 결과는 PASS 또는 FAIL이어야 합니다.",
        )

    completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")

            process_target = connection.execute(
                """
                SELECT
                    ps.serial_no,
                    ps.status AS serial_status,
                    ps.started_at AS serial_started_at,
                    wo.work_order_id,
                    wo.work_order_no,
                    wo.status AS work_order_status,
                    wo.started_at AS work_order_started_at,
                    rs.routing_step_id,
                    rs.sequence_no,
                    p.process_code,
                    p.process_name
                FROM product_serial AS ps
                JOIN work_order AS wo
                ON wo.work_order_id = ps.work_order_id
                JOIN routing_step AS rs
                ON rs.product_item_id = wo.product_item_id
                AND rs.is_active = 1
                AND rs.is_required = 1
                JOIN process AS p
                ON p.process_id = rs.process_id
                WHERE ps.product_serial_id = ?
                AND rs.routing_step_id = ?
                AND ps.status IN ('CREATED', 'IN_PROGRESS')
                AND wo.status IN ('PLANNED', 'IN_PROGRESS')
                AND p.process_code NOT IN ('PROC-EOL', 'PROC-COMPLETE')
                AND NOT EXISTS (
                    SELECT 1
                    FROM process_history AS ph
                    WHERE ph.product_serial_id = ps.product_serial_id
                        AND ph.routing_step_id = rs.routing_step_id
                )
                AND rs.routing_step_id = (
                    SELECT rs_next.routing_step_id
                    FROM routing_step AS rs_next
                    WHERE rs_next.product_item_id = wo.product_item_id
                        AND rs_next.is_active = 1
                        AND rs_next.is_required = 1
                        AND NOT EXISTS (
                            SELECT 1
                            FROM process_history AS ph_next
                            WHERE ph_next.product_serial_id =
                                ps.product_serial_id
                            AND ph_next.routing_step_id =
                                rs_next.routing_step_id
                        )
                    ORDER BY rs_next.sequence_no
                    LIMIT 1
                )
                """,
                (
                    product_serial_id,
                    routing_step_id,
                ),
            ).fetchone()

            if process_target is None:
                connection.rollback()
                return ServiceResult(
                    success=False,
                    message=(
                        "선택한 Serial의 현재 등록 가능한 공정이 아니거나 "
                        "이미 실적이 등록되었습니다."
                    ),
                )

            required_materials = connection.execute(
                """
                SELECT
                    b.material_item_id,
                    material.item_name AS material_name,
                    b.required_qty
                FROM product_serial AS ps
                JOIN work_order AS wo
                  ON wo.work_order_id = ps.work_order_id
                JOIN bom AS b
                  ON b.product_item_id = wo.product_item_id
                 AND b.input_routing_step_id = ?
                 AND b.is_active = 1
                JOIN item AS material
                  ON material.item_id = b.material_item_id
                WHERE ps.product_serial_id = ?
                ORDER BY b.material_item_id
                """,
                (
                    routing_step_id,
                    product_serial_id,
                ),
            ).fetchall()

            required_material_ids = {
                row["material_item_id"]
                for row in required_materials
            }

            if set(selected_lot_ids) != required_material_ids:
                connection.rollback()
                return ServiceResult(
                    success=False,
                    message="공정에 필요한 모든 자재의 LOT를 하나씩 선택해주세요.",
                )

            consumption_rows: list[tuple[int, int]] = []

            for material in required_materials:
                material_item_id = material["material_item_id"]
                material_lot_id = selected_lot_ids[material_item_id]
                required_qty = material["required_qty"]

                lot = connection.execute(
                    """
                    SELECT
                        ml.lot_no,
                        ml.material_item_id,
                        ml.status,
                        ml.received_qty
                            - COALESCE(SUM(mc.consumed_qty), 0)
                            AS available_qty
                    FROM material_lot AS ml
                    LEFT JOIN material_consumption AS mc
                      ON mc.material_lot_id = ml.material_lot_id
                    WHERE ml.material_lot_id = ?
                    GROUP BY
                        ml.material_lot_id,
                        ml.lot_no,
                        ml.material_item_id,
                        ml.status,
                        ml.received_qty
                    """,
                    (material_lot_id,),
                ).fetchone()

                if (
                    lot is None
                    or lot["material_item_id"] != material_item_id
                    or lot["status"] != "AVAILABLE"
                ):
                    connection.rollback()
                    return ServiceResult(
                        success=False,
                        message=(
                            f"{material['material_name']}에 선택한 LOT를 "
                            "사용할 수 없습니다."
                        ),
                    )

                if lot["available_qty"] < required_qty:
                    connection.rollback()
                    return ServiceResult(
                        success=False,
                        message=(
                            f"{lot['lot_no']}의 잔여수량이 부족합니다. "
                            f"필요수량: {required_qty}, "
                            f"잔여수량: {lot['available_qty']}"
                        ),
                    )

                consumption_rows.append(
                    (material_lot_id, required_qty)
                )

            cursor = connection.execute(
                """
                INSERT INTO process_history (
                    product_serial_id,
                    routing_step_id,
                    result,
                    started_at,
                    completed_at,
                    remark
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    product_serial_id,
                    routing_step_id,
                    result,
                    completed_at,
                    completed_at,
                    remark.strip() if remark else None,
                ),
            )

            process_history_id = cursor.lastrowid

            for material_lot_id, consumed_qty in consumption_rows:
                connection.execute(
                    """
                    INSERT INTO material_consumption (
                        product_serial_id,
                        material_lot_id,
                        routing_step_id,
                        consumed_qty,
                        consumed_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        product_serial_id,
                        material_lot_id,
                        routing_step_id,
                        consumed_qty,
                        completed_at,
                    ),
                )

            for material_lot_id, _ in consumption_rows:
                connection.execute(
                    """
                    UPDATE material_lot
                    SET status = 'EXHAUSTED'
                    WHERE material_lot_id = ?
                        AND status = 'AVAILABLE'
                        AND received_qty <= (
                            SELECT COALESCE(SUM(mc.consumed_qty), 0)
                            FROM material_consumption AS mc
                            WHERE mc.material_lot_id =
                                material_lot.material_lot_id
                        )
                    """,
                    (material_lot_id,),
                )

            connection.execute(
                """
                UPDATE work_order
                SET
                    status = 'IN_PROGRESS',
                    started_at = COALESCE(started_at, ?)
                WHERE work_order_id = ?
                AND status = 'PLANNED'
                """,
                (
                    completed_at,
                    process_target["work_order_id"],
                ),
            )

            if result == "FAIL":
                connection.execute(
                    """
                    UPDATE product_serial
                    SET
                        status = 'FAIL',
                        started_at = COALESCE(started_at, ?),
                        completed_at = ?
                    WHERE product_serial_id = ?
                    """,
                    (
                        completed_at,
                        completed_at,
                        product_serial_id,
                    ),
                )

                _complete_work_order_if_finished(
                    connection,
                    process_target["work_order_id"],
                )

            else:
                connection.execute(
                    """
                    UPDATE product_serial
                    SET
                        status = 'IN_PROGRESS',
                        started_at = COALESCE(started_at, ?)
                    WHERE product_serial_id = ?
                    """,
                    (
                        completed_at,
                        product_serial_id,
                    ),
                )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()
            return ServiceResult(
                success=False,
                message="공정 실적 저장 중 중복 또는 제약조건 오류가 발생했습니다.",
            )

        except sqlite3.OperationalError:
            connection.rollback()
            return ServiceResult(
                success=False,
                message="공정 실적 저장 중 데이터베이스 처리 오류가 발생했습니다.",
            )

    return ServiceResult(
        success=True,
        message=(
            f"{process_target['serial_no']}의 "
            f"{process_target['process_name']} 실적을 등록했습니다. "
            f"결과: {result}, 실적 ID: {process_history_id}"
        ),
    )

def get_serial_process_history(
    product_serial_id: int,
) -> pd.DataFrame:
    """선택한 제품 Serial의 공정 실적 이력을 조회한다."""

    sql = """
        SELECT
            ph.process_history_id AS "실적 ID",
            rs.sequence_no AS "공정 순서",
            p.process_code AS "공정코드",
            p.process_name AS "공정명",
            ph.result AS "결과",
            ph.started_at AS "시작 일시",
            ph.completed_at AS "완료 일시",
            ph.remark AS "비고"
        FROM process_history AS ph
        JOIN routing_step AS rs
          ON rs.routing_step_id = ph.routing_step_id
        JOIN process AS p
          ON p.process_id = rs.process_id
        WHERE ph.product_serial_id = ?
        ORDER BY
            rs.sequence_no,
            ph.process_history_id
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(product_serial_id,),
        )

def get_serial_material_consumptions(
    product_serial_id: int,
) -> pd.DataFrame:
    """선택한 제품 Serial의 자재 LOT 소비 이력을 조회한다."""

    sql = """
        SELECT
            mc.consumption_id AS "소비 ID",
            rs.sequence_no AS "공정 순서",
            p.process_name AS "투입 공정",
            material.item_code AS "자재코드",
            material.item_name AS "자재명",
            ml.lot_no AS "자재 LOT",
            mc.consumed_qty AS "사용수량",
            mc.consumed_at AS "사용 일시"
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
            mc.consumption_id
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=(product_serial_id,),
        )

def get_eol_ready_serials() -> pd.DataFrame:
    """현재 다음 공정이 EOL 성능 검사인 Serial을 조회한다."""

    sql = """
        SELECT
            ps.product_serial_id,
            ps.serial_no,
            ps.status AS serial_status,
            wo.work_order_id,
            wo.work_order_no,
            product.item_code,
            product.item_name,
            rs.routing_step_id,
            rs.sequence_no,
            p.process_code,
            p.process_name
        FROM product_serial AS ps
        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id
        JOIN item AS product
          ON product.item_id = wo.product_item_id
        JOIN routing_step AS rs
          ON rs.product_item_id = wo.product_item_id
         AND rs.is_active = 1
        JOIN process AS p
          ON p.process_id = rs.process_id
        WHERE ps.status = 'IN_PROGRESS'
          AND wo.status = 'IN_PROGRESS'
          AND p.process_code = 'PROC-EOL'
          AND NOT EXISTS (
              SELECT 1
              FROM process_history AS ph
              WHERE ph.product_serial_id = ps.product_serial_id
                AND ph.routing_step_id = rs.routing_step_id
          )
          AND rs.routing_step_id = (
              SELECT rs_next.routing_step_id
              FROM routing_step AS rs_next
              WHERE rs_next.product_item_id = wo.product_item_id
                AND rs_next.is_active = 1
                AND NOT EXISTS (
                    SELECT 1
                    FROM process_history AS ph_next
                    WHERE ph_next.product_serial_id =
                          ps.product_serial_id
                      AND ph_next.routing_step_id =
                          rs_next.routing_step_id
                )
              ORDER BY rs_next.sequence_no
              LIMIT 1
          )
        ORDER BY
            wo.work_order_no,
            ps.serial_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def evaluate_eol_result(
    *,
    forward_ok: bool,
    reverse_ok: bool,
    forward_time_ms: int,
    reverse_time_ms: int,
    max_current_ma: float,
    position_error_deg: float | None = None,
) -> tuple[str, str | None]:
    """EOL 측정값을 기준으로 PASS 또는 FAIL을 판정한다."""

    if forward_time_ms < 0:
        raise ValueError("정방향 동작 시간은 0 이상이어야 합니다.")

    if reverse_time_ms < 0:
        raise ValueError("역방향 동작 시간은 0 이상이어야 합니다.")

    if max_current_ma < 0:
        raise ValueError("최대 전류는 0 이상이어야 합니다.")

    if (
        position_error_deg is not None
        and position_error_deg < 0
    ):
        raise ValueError("위치 오차는 0 이상이어야 합니다.")

    failure_reasons: list[str] = []

    if not forward_ok:
        failure_reasons.append("정방향 동작 불량")

    if not reverse_ok:
        failure_reasons.append("역방향 동작 불량")

    if forward_time_ms > EOL_MAX_OPERATION_TIME_MS:
        failure_reasons.append(
            f"정방향 동작 시간 초과({forward_time_ms}ms)"
        )

    if reverse_time_ms > EOL_MAX_OPERATION_TIME_MS:
        failure_reasons.append(
            f"역방향 동작 시간 초과({reverse_time_ms}ms)"
        )

    if max_current_ma > EOL_MAX_CURRENT_MA:
        failure_reasons.append(
            f"최대 전류 초과({max_current_ma:g}mA)"
        )

    if (
        position_error_deg is not None
        and position_error_deg > EOL_MAX_POSITION_ERROR_DEG
    ):
        failure_reasons.append(
            f"위치 오차 초과({position_error_deg:g}°)"
        )

    if failure_reasons:
        return "FAIL", ", ".join(failure_reasons)

    return "PASS", None

def register_eol_test_result(
    *,
    product_serial_id: int,
    routing_step_id: int,
    forward_ok: bool,
    reverse_ok: bool,
    forward_time_ms: int,
    reverse_time_ms: int,
    max_current_ma: float,
    target_angle_deg: float | None = None,
    actual_angle_deg: float | None = None,
) -> tuple[str, str | None]:
    """EOL 검사 결과를 등록하고 최종 판정 결과를 반환한다."""

    with get_connection() as connection:
        # 현재 Serial의 다음 미완료 공정과 제품 정보를 조회한다.
        eol_target = connection.execute(
            """
            SELECT
                ps.product_serial_id,
                ps.status AS serial_status,
                ps.work_order_id,
                wo.status AS work_order_status,
                product.item_code,
                rs.routing_step_id,
                p.process_code
            FROM product_serial AS ps
            JOIN work_order AS wo
              ON wo.work_order_id = ps.work_order_id
            JOIN item AS product
              ON product.item_id = wo.product_item_id
            JOIN routing_step AS rs
              ON rs.product_item_id = wo.product_item_id
             AND rs.is_active = 1
             AND rs.is_required = 1
            JOIN process AS p
              ON p.process_id = rs.process_id
            WHERE ps.product_serial_id = ?
              AND rs.routing_step_id = ?
              AND ps.status = 'IN_PROGRESS'
              AND wo.status = 'IN_PROGRESS'
              AND p.process_code = 'PROC-EOL'
              AND NOT EXISTS (
                  SELECT 1
                  FROM process_history AS ph
                  WHERE ph.product_serial_id = ps.product_serial_id
                    AND ph.routing_step_id = rs.routing_step_id
              )
              AND rs.routing_step_id = (
                  SELECT rs_next.routing_step_id
                  FROM routing_step AS rs_next
                  WHERE rs_next.product_item_id = wo.product_item_id
                    AND rs_next.is_active = 1
                    AND rs_next.is_required = 1
                    AND NOT EXISTS (
                        SELECT 1
                        FROM process_history AS ph_next
                        WHERE ph_next.product_serial_id =
                              ps.product_serial_id
                          AND ph_next.routing_step_id =
                              rs_next.routing_step_id
                    )
                  ORDER BY rs_next.sequence_no
                  LIMIT 1
              )
            """,
            (product_serial_id, routing_step_id),
        ).fetchone()

        if eol_target is None:
            raise ValueError(
                "해당 Serial은 현재 EOL 검사를 등록할 수 없습니다."
            )

        work_order_id = eol_target["work_order_id"]
        item_code = eol_target["item_code"]

        # 센서형 제품은 목표 각도와 실제 각도가 모두 필요하다.
        if item_code == "ACT-SENSOR":
            if target_angle_deg is None or actual_angle_deg is None:
                raise ValueError(
                    "센서형 제품은 목표 각도와 실제 각도가 필요합니다."
                )

        # 둘 중 하나만 입력된 경우는 잘못된 입력이다.
        if (target_angle_deg is None) != (actual_angle_deg is None):
            raise ValueError(
                "목표 각도와 실제 각도는 함께 입력해야 합니다."
            )

        position_error_deg: float | None = None

        if (
            target_angle_deg is not None
            and actual_angle_deg is not None
        ):
            position_error_deg = abs(
                target_angle_deg - actual_angle_deg
            )

        result, failure_reason = evaluate_eol_result(
            forward_ok=forward_ok,
            reverse_ok=reverse_ok,
            forward_time_ms=forward_time_ms,
            reverse_time_ms=reverse_time_ms,
            max_current_ma=max_current_ma,
            position_error_deg=position_error_deg,
        )

        # EOL 공정 실적을 먼저 생성한다.
        cursor = connection.execute(
            """
            INSERT INTO process_history (
                product_serial_id,
                routing_step_id,
                result,
                started_at,
                completed_at,
                remark
            )
            VALUES (
                ?,
                ?,
                ?,
                datetime('now', 'localtime'),
                datetime('now', 'localtime'),
                ?
            )
            """,
            (
                product_serial_id,
                routing_step_id,
                result,
                failure_reason,
            ),
        )

        process_history_id = cursor.lastrowid

        # 생성한 공정 실적과 EOL 상세 측정값을 연결한다.
        connection.execute(
            """
            INSERT INTO eol_test_result (
                process_history_id,
                forward_ok,
                reverse_ok,
                forward_time_ms,
                reverse_time_ms,
                max_current_ma,
                target_angle_deg,
                actual_angle_deg,
                position_error_deg,
                result,
                failure_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                process_history_id,
                int(forward_ok),
                int(reverse_ok),
                forward_time_ms,
                reverse_time_ms,
                max_current_ma,
                target_angle_deg,
                actual_angle_deg,
                position_error_deg,
                result,
                failure_reason,
            ),
        )

        # 불합격 제품은 이후 생산 완료 공정으로 진행시키지 않는다.
        if result == "FAIL":
            connection.execute(
                """
                UPDATE product_serial
                SET
                    status = 'FAIL',
                    completed_at = datetime('now', 'localtime')
                WHERE product_serial_id = ?
                """,
                (product_serial_id,),
            )

            _complete_work_order_if_finished(
                connection,
                work_order_id,
            )

    return result, failure_reason

def get_completion_ready_serials() -> pd.DataFrame:
    """현재 다음 공정이 생산 완료인 Serial을 조회한다."""

    sql = """
        SELECT
            ps.product_serial_id,
            ps.serial_no,
            ps.status AS serial_status,
            wo.work_order_id,
            wo.work_order_no,
            product.item_code,
            product.item_name,
            rs.routing_step_id,
            rs.sequence_no,
            p.process_code,
            p.process_name
        FROM product_serial AS ps
        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id
        JOIN item AS product
          ON product.item_id = wo.product_item_id
        JOIN routing_step AS rs
          ON rs.product_item_id = wo.product_item_id
         AND rs.is_active = 1
         AND rs.is_required = 1
        JOIN process AS p
          ON p.process_id = rs.process_id
        WHERE ps.status = 'IN_PROGRESS'
          AND wo.status = 'IN_PROGRESS'
          AND p.process_code = 'PROC-COMPLETE'
          AND NOT EXISTS (
              SELECT 1
              FROM process_history AS ph
              WHERE ph.product_serial_id = ps.product_serial_id
                AND ph.routing_step_id = rs.routing_step_id
          )
          AND rs.routing_step_id = (
              SELECT rs_next.routing_step_id
              FROM routing_step AS rs_next
              WHERE rs_next.product_item_id = wo.product_item_id
                AND rs_next.is_active = 1
                AND rs_next.is_required = 1
                AND NOT EXISTS (
                    SELECT 1
                    FROM process_history AS ph_next
                    WHERE ph_next.product_serial_id =
                          ps.product_serial_id
                      AND ph_next.routing_step_id =
                          rs_next.routing_step_id
                )
              ORDER BY rs_next.sequence_no
              LIMIT 1
          )
        ORDER BY
            wo.work_order_no,
            ps.serial_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def complete_product(
    *,
    product_serial_id: int,
    routing_step_id: int,
) -> None:
    """생산 완료 실적을 등록하고 Serial을 최종 PASS 처리한다."""

    with get_connection() as connection:
        target = connection.execute(
            """
            SELECT
                ps.product_serial_id,
                ps.work_order_id,
                rs.routing_step_id
            FROM product_serial AS ps
            JOIN work_order AS wo
              ON wo.work_order_id = ps.work_order_id
            JOIN routing_step AS rs
              ON rs.product_item_id = wo.product_item_id
             AND rs.is_active = 1
             AND rs.is_required = 1
            JOIN process AS p
              ON p.process_id = rs.process_id
            WHERE ps.product_serial_id = ?
              AND rs.routing_step_id = ?
              AND ps.status = 'IN_PROGRESS'
              AND wo.status = 'IN_PROGRESS'
              AND p.process_code = 'PROC-COMPLETE'
              AND NOT EXISTS (
                  SELECT 1
                  FROM process_history AS ph
                  WHERE ph.product_serial_id = ps.product_serial_id
                    AND ph.routing_step_id = rs.routing_step_id
              )
              AND rs.routing_step_id = (
                  SELECT rs_next.routing_step_id
                  FROM routing_step AS rs_next
                  WHERE rs_next.product_item_id = wo.product_item_id
                    AND rs_next.is_active = 1
                    AND rs_next.is_required = 1
                    AND NOT EXISTS (
                        SELECT 1
                        FROM process_history AS ph_next
                        WHERE ph_next.product_serial_id =
                              ps.product_serial_id
                          AND ph_next.routing_step_id =
                              rs_next.routing_step_id
                    )
                  ORDER BY rs_next.sequence_no
                  LIMIT 1
              )
            """,
            (product_serial_id, routing_step_id),
        ).fetchone()

        if target is None:
            raise ValueError(
                "해당 Serial은 현재 생산 완료 처리할 수 없습니다."
            )

        work_order_id = target["work_order_id"]

        # 생산 완료 공정 실적을 등록한다.
        connection.execute(
            """
            INSERT INTO process_history (
                product_serial_id,
                routing_step_id,
                result,
                started_at,
                completed_at,
                remark
            )
            VALUES (
                ?,
                ?,
                'PASS',
                datetime('now', 'localtime'),
                datetime('now', 'localtime'),
                NULL
            )
            """,
            (product_serial_id, routing_step_id),
        )

        # Serial을 최종 합격 상태로 변경한다.
        connection.execute(
            """
            UPDATE product_serial
            SET
                status = 'PASS',
                completed_at = datetime('now', 'localtime')
            WHERE product_serial_id = ?
            """,
            (product_serial_id,),
        )
        _complete_work_order_if_finished(
            connection,
            work_order_id,
        )
        
def _complete_work_order_if_finished(
    connection,
    work_order_id: int,
) -> bool:
    """계획 수량만큼 발급된 모든 Serial이 종료되면 작업지시를 완료한다."""

    counts = connection.execute(
        """
        SELECT
            wo.planned_qty,
            COUNT(ps.product_serial_id) AS issued_count,
            SUM(
                CASE
                    WHEN ps.status IN ('PASS', 'FAIL') THEN 1
                    ELSE 0
                END
            ) AS finished_count
        FROM work_order AS wo
        LEFT JOIN product_serial AS ps
          ON ps.work_order_id = wo.work_order_id
        WHERE wo.work_order_id = ?
        GROUP BY
            wo.work_order_id,
            wo.planned_qty
        """,
        (work_order_id,),
    ).fetchone()

    if counts is None:
        raise ValueError("작업지시를 찾을 수 없습니다.")

    planned_qty = counts["planned_qty"]
    issued_count = counts["issued_count"]
    finished_count = counts["finished_count"] or 0

    if issued_count != planned_qty:
        return False

    if finished_count != planned_qty:
        return False

    cursor = connection.execute(
        """
        UPDATE work_order
        SET
            status = 'COMPLETED',
            completed_at = datetime('now', 'localtime')
        WHERE work_order_id = ?
          AND status = 'IN_PROGRESS'
        """,
        (work_order_id,),
    )

    return cursor.rowcount == 1

def get_history_serials() -> pd.DataFrame:
    """공정 및 자재 소비 이력을 조회할 전체 제품 Serial 목록을 반환한다."""

    sql = """
        SELECT
            ps.product_serial_id,
            ps.serial_no,
            ps.status AS serial_status,
            wo.work_order_no,
            i.item_code,
            i.item_name,
            ps.created_at
        FROM product_serial AS ps
        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id
        JOIN item AS i
          ON i.item_id = wo.product_item_id
        ORDER BY
            ps.created_at DESC,
            ps.product_serial_id DESC
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
        )

