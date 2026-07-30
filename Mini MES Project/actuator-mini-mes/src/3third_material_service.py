from src.db import get_connection
from datetime import datetime

# PROC-MOTOR 공정에서 실제로 사용한 자재 LOT 기록(DC 모터, 하우징)
def register_material_consumption(
    serial_no: str,
    process_code: str,
    lot_no: str,
    consumed_qty: int,
) -> int:
    serial_no = serial_no.strip()
    process_code = process_code.strip()
    lot_no = lot_no.strip()

    if not serial_no:
        raise ValueError("Serial 번호를 입력해야 합니다.")

    if not process_code:
        raise ValueError("공정 코드를 입력해야 합니다.")

    if not lot_no:
        raise ValueError("자재 LOT 번호를 입력해야 합니다.")

    if not isinstance(consumed_qty, int) or isinstance(consumed_qty, bool):
        raise ValueError("소비수량은 정수여야 합니다.")

    if consumed_qty <= 0:
        raise ValueError("소비수량은 1 이상이어야 합니다.")

    with get_connection() as connection:
        production_info = connection.execute(
            """
            SELECT
                ps.product_serial_id,
                ps.status AS serial_status,
                wo.product_item_id,
                rs.routing_step_id,
                p.process_name,
                ph.result AS process_result
            FROM product_serial AS ps
            JOIN work_order AS wo
                ON wo.work_order_id = ps.work_order_id
            JOIN routing_step AS rs
                ON rs.product_item_id = wo.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            LEFT JOIN process_history AS ph
                ON ph.product_serial_id = ps.product_serial_id
               AND ph.routing_step_id = rs.routing_step_id
            WHERE ps.serial_no = ?
              AND p.process_code = ?
              AND rs.is_active = 1
            """,
            (serial_no, process_code),
        ).fetchone()

        if production_info is None:
            raise ValueError(
                "Serial의 제품 라우팅에서 공정을 찾을 수 없습니다: "
                f"{process_code}"
            )

        if production_info["serial_status"] != "IN_PROGRESS":
            raise ValueError(
                "자재를 투입할 수 없는 Serial 상태입니다: "
                f"{production_info['serial_status']}"
            )

        if production_info["process_result"] is not None:
            raise ValueError(
                f"이미 실적이 등록된 공정에는 자재를 투입할 수 없습니다: "
                f"{process_code}"
            )

        current_routing_step = connection.execute(
            """
            SELECT
                rs.routing_step_id,
                rs.sequence_no,
                p.process_code,
                p.process_name
            FROM routing_step AS rs
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE rs.product_item_id = ?
            AND rs.is_active = 1
            AND rs.is_required = 1
            AND NOT EXISTS (
                SELECT 1
                FROM process_history AS ph
                WHERE ph.product_serial_id = ?
                    AND ph.routing_step_id = rs.routing_step_id
            )
            ORDER BY rs.sequence_no
            LIMIT 1
            """,
            (
                production_info["product_item_id"],
                production_info["product_serial_id"],
            ),
        ).fetchone()

        if current_routing_step is None:
            raise ValueError("현재 진행할 수 있는 필수 공정이 없습니다.")

        if (
            current_routing_step["routing_step_id"]
            != production_info["routing_step_id"]
        ):
            raise ValueError(
                "현재 자재를 투입해야 할 공정은 "
                f"{current_routing_step['process_code']} "
                f"({current_routing_step['process_name']})입니다."
            )

        material_lot = connection.execute(
            """
            SELECT
                ml.material_lot_id,
                ml.material_item_id,
                ml.received_qty,
                ml.status,
                i.item_code,
                i.item_name
            FROM material_lot AS ml
            JOIN item AS i
                ON i.item_id = ml.material_item_id
            WHERE ml.lot_no = ?
            """,
            (lot_no,),
        ).fetchone()

        if material_lot is None:
            raise ValueError(
                f"자재 LOT를 찾을 수 없습니다: {lot_no}"
            )

        if material_lot["status"] != "AVAILABLE":
            raise ValueError(
                "사용할 수 없는 자재 LOT 상태입니다: "
                f"{material_lot['status']}"
            )

        bom = connection.execute(
            """
            SELECT
                bom_id,
                required_qty
            FROM bom
            WHERE product_item_id = ?
              AND material_item_id = ?
              AND input_routing_step_id = ?
              AND is_active = 1
            """,
            (
                production_info["product_item_id"],
                material_lot["material_item_id"],
                production_info["routing_step_id"],
            ),
        ).fetchone()

        if bom is None:
            raise ValueError(
                f"{material_lot['item_code']}은(는) "
                f"{process_code} 공정의 BOM 자재가 아닙니다."
            )

        if consumed_qty != bom["required_qty"]:
            raise ValueError(
                "BOM 기준 투입수량과 일치하지 않습니다. "
                f"필요수량: {bom['required_qty']}, "
                f"입력수량: {consumed_qty}"
            )

        consumed_total = connection.execute(
            """
            SELECT COALESCE(SUM(consumed_qty), 0) AS total
            FROM material_consumption
            WHERE material_lot_id = ?
            """,
            (material_lot["material_lot_id"],),
        ).fetchone()["total"]

        # 잔여수량 = 입고수량 - 지금까지의 총 소비수량
        remaining_qty = (
            material_lot["received_qty"] - consumed_total
        )

        if remaining_qty < consumed_qty:
            raise ValueError(
                "자재 LOT의 재고가 부족합니다. "
                f"가용수량: {remaining_qty}, "
                f"요청수량: {consumed_qty}"
            )

        duplicated_consumption = connection.execute(
            """
            SELECT consumption_id
            FROM material_consumption
            WHERE product_serial_id = ?
              AND material_lot_id = ?
              AND routing_step_id = ?
            """,
            (
                production_info["product_serial_id"],
                material_lot["material_lot_id"],
                production_info["routing_step_id"],
            ),
        ).fetchone()

        if duplicated_consumption is not None:
            raise ValueError(
                f"이미 투입된 자재 LOT입니다: {lot_no}"
            )

        cursor = connection.execute(
            """
            INSERT INTO material_consumption (
                product_serial_id,
                material_lot_id,
                routing_step_id,
                consumed_qty
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                production_info["product_serial_id"],
                material_lot["material_lot_id"],
                production_info["routing_step_id"],
                consumed_qty,
            ),
        )

        remaining_after_consumption = remaining_qty - consumed_qty

        if remaining_after_consumption == 0:
            connection.execute(
                """
                UPDATE material_lot
                SET status = 'EXHAUSTED'
                WHERE material_lot_id = ?
                """,
                (material_lot["material_lot_id"],),
            )

        return cursor.lastrowid

# 생산을 시작한 Serial에 첫 번째 공정인 모터 조립 실적 등록
def register_process_result(
        serial_no: str,
        process_code: str,
        result: str,
        remark: str | None = None,
) -> int:
    serial_no = serial_no.strip()
    process_code = process_code.strip()
    result = result.strip().upper()

    if not serial_no:
        raise ValueError('Serial 번호를 입력해야 합니다.')

    if not process_code:
        raise ValueError('공정 코드를 입력해야 합니다.')

    if result not in ("PASS", "FAIL"):
        raise ValueError('공정 결과는 PASS 또는 FAIL이어야 합니다.')

    if process_code == "PROC-EOL":
        raise ValueError("EOL 공정은 register_eol_test_result()로 등록해야 합니다.")

    # Serial 존재 여부 확인
    with get_connection() as connection:
        product_serial = connection.execute(
            """
            SELECT
                ps.product_serial_id,
                ps.status AS serial_status,
                wo.product_item_id
            FROM product_serial AS ps
            JOIN work_order AS wo
                ON wo.work_order_id = ps.work_order_id
            WHERE ps.serial_no = ?
            """,
            (serial_no,),
        ).fetchone()

        if product_serial is None:
            raise ValueError(
                f'Serial 번호를 찾을 수 없습니다 : {serial_no}'
            )

        if product_serial["serial_status"] != "IN_PROGRESS":
            raise ValueError(
                '공정 실적을 등록할 수 없는 Serial 상태입니다: '
                f"{product_serial['serial_status']}"
            )

        # 제품 routing 조회
        # 현재 Serial에 이미 실적이 등록된 공정은 제외한다.
        # 남아있는 공정 중 순서가 가장 빠른 한 건만 가져온다.
        # 모터 조립 전에 기어 조립부터 등록하려는 작업 차단 가능
        next_routing_step = connection.execute(
            """
            SELECT
                rs.routing_step_id,
                rs.sequence_no,
                p.process_code,
                p.process_name
            FROM routing_step AS rs
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE rs.product_item_id = ?
              AND rs.is_active = 1
              AND rs.is_required = 1
              AND NOT EXISTS (
                    SELECT 1
                    FROM process_history AS ph
                    WHERE ph.product_serial_id = ?
                      AND ph.routing_step_id = rs.routing_step_id
              )
            ORDER BY rs.sequence_no
            LIMIT 1
            """,
            (
                product_serial["product_item_id"],
                product_serial["product_serial_id"],
            ),
        ).fetchone()

        if next_routing_step is None:
            raise ValueError(
                '등록할 필수 공정이 없습니다. 모든 필수 공정이 등록되었는지 확인하세요.'
            )

        if next_routing_step["process_code"] != process_code:
            raise ValueError(
                "현재 등록해야 할 공정은 "
                f"{next_routing_step['process_code']}"
                f"({next_routing_step['process_name']})입니다."
            )

        # PASS 등록 전, 현재 공정에 필요한 BOM 자재가
        # 모두 투입되었는지 확인
        if result == "PASS":
            missing_materials = connection.execute(
                """
                SELECT
                    material.item_code,
                    material.item_name,
                    b.required_qty,
                    COALESCE(SUM(mc.consumed_qty), 0) AS consumed_qty
                FROM bom AS b
                JOIN item AS material
                    ON material.item_id = b.material_item_id
                LEFT JOIN material_lot AS ml
                    ON ml.material_item_id = b.material_item_id
                LEFT JOIN material_consumption AS mc
                    ON mc.material_lot_id = ml.material_lot_id
                   AND mc.product_serial_id = ?
                   AND mc.routing_step_id = b.input_routing_step_id
                WHERE b.product_item_id = ?
                  AND b.input_routing_step_id = ?
                  AND b.is_active = 1
                GROUP BY
                    b.bom_id,
                    material.item_code,
                    material.item_name,
                    b.required_qty
                HAVING
                    COALESCE(SUM(mc.consumed_qty), 0)
                    < b.required_qty
                """,
                (
                    product_serial["product_serial_id"],
                    product_serial["product_item_id"],
                    next_routing_step["routing_step_id"],
                ),
            ).fetchall()

            if missing_materials:
                details = ", ".join(
                    f"{row['item_code']} "
                    f"(필요 {row['required_qty']}, "
                    f"투입 {row['consumed_qty']})"
                    for row in missing_materials
                )

                raise ValueError(
                    f"필수 BOM 자재 투입이 부족합니다: {details}"
                )

        # process_history에 실적 저장
        cursor = connection.execute(
            """
            INSERT INTO process_history(
                product_serial_id,
                routing_step_id,
                result,
                started_at,
                completed_at,
                remark
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
            """,
            (
                product_serial["product_serial_id"],
                next_routing_step["routing_step_id"],
                result,
                remark,
            ),
        )

        # PASS와 FAIL을 모두 “등록 완료된 공정”으로 판단한다.
        # 따라서 FAIL을 등록해도 다음 공정으로 넘어갈 수 있다.
        # 추후 PASS → 다음 공정 진행, FAIL → 다음 공정 진행 차단 또는 재작업 처리

        return cursor.lastrowid

def get_material_lot_inventory():
    """자재 LOT별 입고량, 누적 투입량, 잔여 수량을 조회한다."""

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                ml.material_lot_id,
                ml.lot_no,
                i.item_code,
                i.item_name,
                ml.received_qty,
                COALESCE(SUM(mc.consumed_qty), 0) AS consumed_qty,
                ml.received_qty
                    - COALESCE(SUM(mc.consumed_qty), 0) AS remaining_qty,
                ml.status,
                ml.received_date
            FROM material_lot AS ml
            JOIN item AS i
                ON i.item_id = ml.material_item_id
            LEFT JOIN material_consumption AS mc
                ON mc.material_lot_id = ml.material_lot_id
            GROUP BY
                ml.material_lot_id,
                ml.lot_no,
                i.item_code,
                i.item_name,
                ml.received_qty,
                ml.status,
                ml.received_date
            ORDER BY
                i.item_code,
                ml.received_date,
                ml.lot_no
            """
        ).fetchall()
