from datetime import date, timedelta

from src.db import get_connection
from src.first_work_order_service import (
    create_work_order_with_serials,
)
from src.second_production_service import start_product_serial
from src.third_material_service import (
    register_material_consumption,
    register_process_result,
)
from src.fourth_eol_service import (
    register_eol_test_result,
    complete_production,
)


PRODUCT_CODE = "ACT-SENSOR"
WORK_ORDER_NO = "WO-PYTEST-INTEGRATION-001"
PLANNED_QTY = 2


def get_normal_processes(product_code: str):
    """EOL과 생산 완료를 제외한 필수 일반 공정을 조회한다."""

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                rs.routing_step_id,
                rs.sequence_no,
                p.process_code,
                p.process_name
            FROM routing_step AS rs
            JOIN item AS product
                ON product.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE product.item_code = ?
              AND rs.is_active = 1
              AND rs.is_required = 1
              AND p.process_code NOT IN (
                    'PROC-EOL',
                    'PROC-COMPLETE'
              )
            ORDER BY rs.sequence_no
            """,
            (product_code,),
        ).fetchall()


def get_step_materials(routing_step_id: int):
    """공정별 BOM 자재에 사용할 수 있는 가장 오래된 LOT를 조회한다."""

    with get_connection() as connection:
        return connection.execute(
            """
            WITH available_lots AS (
                SELECT
                    material.item_code AS material_code,
                    b.required_qty,
                    ml.lot_no,
                    ml.received_qty
                        - COALESCE(used.consumed_qty, 0)
                        AS remaining_qty,
                    ROW_NUMBER() OVER (
                        PARTITION BY b.bom_id
                        ORDER BY
                            ml.received_date,
                            ml.material_lot_id
                    ) AS lot_rank
                FROM bom AS b
                JOIN item AS material
                    ON material.item_id = b.material_item_id
                JOIN material_lot AS ml
                    ON ml.material_item_id = b.material_item_id
                LEFT JOIN (
                    SELECT
                        material_lot_id,
                        SUM(consumed_qty) AS consumed_qty
                    FROM material_consumption
                    GROUP BY material_lot_id
                ) AS used
                    ON used.material_lot_id = ml.material_lot_id
                WHERE b.input_routing_step_id = ?
                  AND b.is_active = 1
                  AND ml.status = 'AVAILABLE'
                  AND (
                        ml.received_qty
                        - COALESCE(used.consumed_qty, 0)
                      ) >= b.required_qty
            )
            SELECT
                material_code,
                required_qty,
                lot_no,
                remaining_qty
            FROM available_lots
            WHERE lot_rank = 1
            ORDER BY material_code
            """,
            (routing_step_id,),
        ).fetchall()


def run_normal_processes(serial_no: str):
    """자재를 투입하고 EOL 이전의 일반 공정을 모두 PASS 처리한다."""

    processes = get_normal_processes(PRODUCT_CODE)

    assert processes, "필수 일반 공정이 등록되어 있지 않습니다."

    for process in processes:
        materials = get_step_materials(
            process["routing_step_id"]
        )

        for material in materials:
            consumption_id = register_material_consumption(
                serial_no=serial_no,
                process_code=process["process_code"],
                lot_no=material["lot_no"],
                consumed_qty=material["required_qty"],
            )

            assert isinstance(consumption_id, int)
            assert consumption_id > 0

        process_history_id = register_process_result(
            serial_no=serial_no,
            process_code=process["process_code"],
            result="PASS",
            remark="pytest 통합 테스트 정상 처리",
        )

        assert isinstance(process_history_id, int)
        assert process_history_id > 0


def test_complete_production_flow_with_pass_and_fail(test_db):
    """
    Serial 2개를 생산하여 각각 EOL PASS와 FAIL로 종료하고,
    작업지시 및 생산 이력을 검증한다.
    """

    due_date = (date.today() + timedelta(days=7)).isoformat()

    # 1. 작업지시와 Serial 2개 생성
    work_order_id, serial_numbers = create_work_order_with_serials(
        work_order_no=WORK_ORDER_NO,
        product_item_code=PRODUCT_CODE,
        planned_qty=PLANNED_QTY,
        due_date=due_date,
    )

    assert isinstance(work_order_id, int)
    assert work_order_id > 0
    assert serial_numbers == [
        f"{WORK_ORDER_NO}-S001",
        f"{WORK_ORDER_NO}-S002",
    ]

    pass_serial = serial_numbers[0]
    fail_serial = serial_numbers[1]

    # 2. 첫 번째 Serial: EOL PASS 후 생산 완료
    start_product_serial(pass_serial)
    run_normal_processes(pass_serial)

    pass_eol_result = register_eol_test_result(
        serial_no=pass_serial,
        forward_ok=True,
        reverse_ok=True,
        forward_time_ms=800,
        reverse_time_ms=820,
        max_current_ma=1200.0,
        target_angle_deg=90.0,
        actual_angle_deg=89.5,
    )

    assert pass_eol_result["result"] == "PASS"
    assert pass_eol_result["position_error_deg"] == 0.5
    assert pass_eol_result["failure_reason"] is None

    completion_result = complete_production(pass_serial)

    assert completion_result["serial_no"] == pass_serial
    assert completion_result["process_code"] == "PROC-COMPLETE"
    assert completion_result["result"] == "PASS"
    assert completion_result["serial_status"] == "PASS"

    # 3. 두 번째 Serial: EOL FAIL
    start_product_serial(fail_serial)
    run_normal_processes(fail_serial)

    fail_eol_result = register_eol_test_result(
        serial_no=fail_serial,
        forward_ok=False,
        reverse_ok=True,
        forward_time_ms=1100,
        reverse_time_ms=850,
        max_current_ma=1600.0,
        target_angle_deg=90.0,
        actual_angle_deg=86.0,
    )

    assert fail_eol_result["result"] == "FAIL"
    assert fail_eol_result["position_error_deg"] == 4.0
    assert fail_eol_result["failure_reason"] is not None
    assert "정방향 작동 불량" in fail_eol_result["failure_reason"]
    assert "최대 전류 초과" in fail_eol_result["failure_reason"]
    assert "위치 오차 초과" in fail_eol_result["failure_reason"]

    # 4. 최종 DB 상태 확인
    with get_connection() as connection:
        work_order = connection.execute(
            """
            SELECT
                work_order_no,
                planned_qty,
                status,
                started_at,
                completed_at
            FROM work_order
            WHERE work_order_id = ?
            """,
            (work_order_id,),
        ).fetchone()

        serial_results = connection.execute(
            """
            SELECT
                serial_no,
                status,
                started_at,
                completed_at
            FROM product_serial
            WHERE work_order_id = ?
            ORDER BY product_serial_id
            """,
            (work_order_id,),
        ).fetchall()

        result_summary = connection.execute(
            """
            SELECT
                status,
                COUNT(*) AS quantity
            FROM product_serial
            WHERE work_order_id = ?
            GROUP BY status
            """,
            (work_order_id,),
        ).fetchall()

        process_count = connection.execute(
            """
            SELECT
                ps.serial_no,
                COUNT(ph.process_history_id) AS process_count
            FROM product_serial AS ps
            LEFT JOIN process_history AS ph
                ON ph.product_serial_id = ps.product_serial_id
            WHERE ps.work_order_id = ?
            GROUP BY
                ps.product_serial_id,
                ps.serial_no
            ORDER BY ps.product_serial_id
            """,
            (work_order_id,),
        ).fetchall()

        eol_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM eol_test_result AS etr
            JOIN process_history AS ph
                ON ph.process_history_id = etr.process_history_id
            JOIN product_serial AS ps
                ON ps.product_serial_id = ph.product_serial_id
            WHERE ps.work_order_id = ?
            """,
            (work_order_id,),
        ).fetchone()[0]

    # 5. 작업지시 검증
    assert work_order is not None
    assert work_order["work_order_no"] == WORK_ORDER_NO
    assert work_order["planned_qty"] == 2
    assert work_order["status"] == "COMPLETED"
    assert work_order["started_at"] is not None
    assert work_order["completed_at"] is not None

    # 6. Serial 상태 검증
    assert len(serial_results) == 2

    serial_statuses = {
        row["serial_no"]: row["status"]
        for row in serial_results
    }

    assert serial_statuses == {
        pass_serial: "PASS",
        fail_serial: "FAIL",
    }

    for serial in serial_results:
        assert serial["started_at"] is not None
        assert serial["completed_at"] is not None

    # 7. PASS·FAIL 수량 검증
    summary = {
        row["status"]: row["quantity"]
        for row in result_summary
    }

    assert summary == {
        "PASS": 1,
        "FAIL": 1,
    }

    # 8. 공정 및 EOL 이력 검증
    process_counts = {
        row["serial_no"]: row["process_count"]
        for row in process_count
    }

    # PASS 제품은 PROC-COMPLETE 이력이 하나 더 존재한다.
    assert process_counts[pass_serial] == 7
    assert process_counts[fail_serial] == 6
    assert eol_count == 2
