from src.db import get_connection
from datetime import datetime

# 입력한 품목 코드가 현재 생산할 수 있는 완제품인가?
def find_active_product(product_item_code: str):
    product_item_code = product_item_code.strip() # 문자열 앞뒤 공백 제거

    if not product_item_code:
        raise ValueError('제품 품목 코드를 입력해야 합니다.') # 빈 값 검사

    with get_connection() as connection: # DB 연결
        product = connection.execute(
        """
        SELECT
            item_id,
            item_code,
            item_name
        FROM item
        WHERE item_code = ?
          AND item_type = 'PRODUCT'
          AND is_active = 1
        """,
        (product_item_code,), # ?에 들어갈 값
        # 값이 하나뿐이어도 뒤에 쉼표가 있어야 문자열이 아니라 SQL에
        #전달할 값이 담긴 튜플이 됨
        ).fetchone() # SQL 조회 결과 중 한 행을 가져옴

    if product is None:
        raise ValueError(
            f'생산 가능한 완제품 품목을 찾을 수 없습니다: {product_item_code}'
        )

    return product


# create_work_order_only() + create_product_serials()
# 작업 지시 생성과 Serial 생성을 하나의 트랜잭션으로 묶는 함수
def create_work_order_with_serials(
        work_order_no: str,
        product_item_code: str,
        planned_qty: int,
        due_date: str,
) -> tuple[int, list[str]]:
    # work_order_id, created_serial_number를 함께 반환한다.
    work_order_no = work_order_no.strip()

    if not work_order_no:
        raise ValueError('작업 지시 번호를 입력해야 합니다.')

    if not isinstance(planned_qty, int) or isinstance(planned_qty, bool):
        raise ValueError('계획 수량은 정수여야 합니다.')

    if planned_qty <= 0:
        raise ValueError('계획 수량은 1 이상이어야 합니다.')

    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except (TypeError, ValueError) as error:
        raise ValueError(
            '납기일은 YYYY-MM-DD 형식의 올바른 날짜여야 합니다.'
        ) from error

    product = find_active_product(product_item_code)

    with get_connection() as connection: # 하나의 연결 블록에서 두 작업 처리
        # Serial을 생성하다가 오류가 발생하면 with 블록이 정상적으로 끝나지 않아,
        # 같은 트랜잭션에서 먼저 삽입한 작업 지시도 함께 롤백 -> 원자성(Atomicity)
        duplicated_order = connection.execute(
            """
            SELECT work_order_id
            FROM work_order
            WHERE work_order_no = ?
            """,
            (work_order_no,),
        ).fetchone()

        if duplicated_order is not None:
            raise ValueError(
                f'이미 등록된 작업 지시 번호입니다 : {work_order_no}'
            )

        cursor = connection.execute (
            """
            INSERT INTO work_order (
                work_order_no,
                product_item_id,
                planned_qty,
                due_date
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                work_order_no,
                product["item_id"],
                planned_qty,
                due_date,
            ),
        )

        work_order_id = cursor.lastrowid
        created_serial_numbers = []

        for sequence in range(1, planned_qty + 1):
            serial_no = f"{work_order_no}-S{sequence:03d}"

            connection.execute(
                """
                INSERT INTO product_serial (
                    serial_no,
                    work_order_id
                )
                VALUES (?, ?)
                """,
                (serial_no, work_order_id),
            )

            created_serial_numbers.append(serial_no)

    # 작업 지시와 Serial 번호가 발급만 된거지, 공정이 시작된 것은 아님.
    return work_order_id, created_serial_numbers

# 공정 시작, Serial 한 개 생산
# 작업지시: PLANNED → IN_PROGRESS
# 제품 Serial: CREATED → IN_PROGRESS
def start_product_serial(serial_no: str) -> None:
    serial_no = serial_no.strip()

    if not serial_no:
        raise ValueError('Serial 번호를 입력해야 합니다.')

    with get_connection() as connection:
        product_serial = connection.execute(
            """
            SELECT
                ps.product_serial_id,
                ps.work_order_id,
                ps.status AS serial_status,
                wo.status AS work_order_status
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

        if product_serial["serial_status"] != "CREATED":
            raise ValueError(
                '생산을 시작할 수 없는 Serial 상태입니다: '
                f'{product_serial['serial_status']}'
            )

        if product_serial["work_order_status"] == "CANCELLED":
            raise ValueError('취소된 작업 지시의 생산은 시작할 수 없습니다.')

        if product_serial["work_order_status"] == "COMPLETED":
            raise ValueError('완료된 작업 지시의 생산은 시작할 수 없습니다.')

        # Serial을 IN_PROGRESS로 변경/Serial이 실제 생산에 투입되었다.
        connection.execute(
            """
            UPDATE product_serial
            SET
                status = 'IN_PROGRESS',
                started_at = CURRENT_TIMESTAMP
            WHERE product_serial_id = ?
            """,
            (product_serial["product_serial_id"],),
        )

        # Serial이 생산에 투입 되었으니, 작업 지시도 함께 IN_PROGRESS로 변경
        if product_serial["work_order_status"] == "PLANNED":
            connection.execute(
                """
                UPDATE work_order
                SET
                    status = 'IN_PROGRESS',
                    started_at = CURRENT_TIMESTAMP
                WHERE work_order_id = ?
                """,
                (product_serial["work_order_id"],),
            )


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
                '현재 등록해야 할 공정은 '
                f'{next_routing_step['process_code']}'
                f'({next_routing_step['process_name']})입니다.'
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


# PROC-MOTOR 공정에서 실제로 사용한 자재 LOT 기록(DC 모처, 하우징)
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
