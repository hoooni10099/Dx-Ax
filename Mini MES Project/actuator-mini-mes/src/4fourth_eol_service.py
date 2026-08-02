from src.db import get_connection
from src.first_work_order_service import update_work_order_status

# Mini MES 학습용 EOL 합격 기준
MAX_OPERATION_TIME_MS = 1000
MAX_CURRENT_MA = 1500.0
MAX_POSITION_ERROR_DEG = 2.0

# EOL 입력값 검증과 자동 판정 로직
def register_eol_test_result(

        serial_no: str,
        forward_ok: bool,
        reverse_ok: bool,
        forward_time_ms: int,
        reverse_time_ms: int,
        max_current_ma: float,
        target_angle_deg: float | None = None,
        actual_angle_deg: float | None = None,
) -> dict:
    """
    EOL 측정값을 검증하고 PASS/FAIL을 자동 판정한 뒤,
    공정 이력과 EOL 검사 결과를 하나의 트랜잭션으로 저장한다.
    """

    # -------------------------
    # 1. 기본 입력값 검증
    # -------------------------
    serial_no = serial_no.strip()

    if not serial_no:
        raise ValueError("Serial 번호를 입력하세요.")

    if not isinstance(forward_ok, bool):
        raise ValueError(
            "정방향 작동 여부는 True 또는 False여야 합니다."
        )

    if not isinstance(reverse_ok, bool):
        raise ValueError(
            "역방향 작동 여부는 True 또는 False여야 합니다."
        )

    if (
        isinstance(forward_time_ms, bool)
        or not isinstance(forward_time_ms, int)
    ):
        raise ValueError("정방향 작동 시간은 정수여야 합니다.")

    if (
        isinstance(reverse_time_ms, bool)
        or not isinstance(reverse_time_ms, int)
    ):
        raise ValueError("역방향 작동 시간은 정수여야 합니다.")

    if forward_time_ms <= 0:
        raise ValueError(
            "정방향 작동 시간은 0보다 커야 합니다."
        )

    if reverse_time_ms <= 0:
        raise ValueError(
            "역방향 작동 시간은 0보다 커야 합니다."
        )

    if (
        isinstance(max_current_ma, bool)
        or not isinstance(max_current_ma, (int, float))
    ):
        raise ValueError("최대 전류는 숫자여야 합니다.")

    if max_current_ma <= 0:
        raise ValueError("최대 전류는 0보다 커야 합니다.")

    # 목표 각도와 실제 각도는 둘 다 입력하거나
    # 둘 다 입력하지 않아야 한다.
    if (target_angle_deg is None) != (actual_angle_deg is None):
        raise ValueError(
            "목표 각도와 실제 각도는 모두 입력하거나 "
            "모두 입력하지 않아야 합니다."
        )

    if target_angle_deg is not None:
        if (
            isinstance(target_angle_deg, bool)
            or not isinstance(target_angle_deg, (int, float))
        ):
            raise ValueError("목표 각도는 숫자여야 합니다.")

        if (
            isinstance(actual_angle_deg, bool)
            or not isinstance(actual_angle_deg, (int, float))
        ):
            raise ValueError("실제 각도는 숫자여야 합니다.")

    # -------------------------
    # 2. 위치 오차 계산
    # -------------------------
    position_error_deg = None

    if target_angle_deg is not None and actual_angle_deg is not None:
        target_angle_deg = float(target_angle_deg)
        actual_angle_deg = float(actual_angle_deg)

        position_error_deg = abs(
            target_angle_deg - actual_angle_deg
        )

    # -------------------------
    # 3. EOL PASS/FAIL 자동 판정
    # -------------------------
    failures = []

    if not forward_ok:
        failures.append("정방향 작동 불량")

    if not reverse_ok:
        failures.append("역방향 작동 불량")

    if forward_time_ms > MAX_OPERATION_TIME_MS:
        failures.append(
            f"정방향 작동 시간 초과: {forward_time_ms}ms"
        )

    if reverse_time_ms > MAX_OPERATION_TIME_MS:
        failures.append(
            f"역방향 작동 시간 초과: {reverse_time_ms}ms"
        )

    if max_current_ma > MAX_CURRENT_MA:
        failures.append(
            f"최대 전류 초과: {max_current_ma}mA"
        )

    if (
        position_error_deg is not None
        and position_error_deg > MAX_POSITION_ERROR_DEG
    ):
        failures.append(
            f"위치 오차 초과: {position_error_deg:.2f}도"
        )

    result = "FAIL" if failures else "PASS"
    failure_reason = "; ".join(failures) if failures else None

    # -------------------------
    # 4. DB 조회 및 저장
    # -------------------------
    with get_connection() as connection:
        # Serial과 제품 정보 조회
        product_serial = connection.execute(
            """
            SELECT
                ps.product_serial_id,
                ps.work_order_id,
                ps.status AS serial_status,
                wo.product_item_id,
                i.item_code AS product_code,
                i.item_name AS product_name
            FROM product_serial AS ps
            JOIN work_order AS wo
                ON wo.work_order_id = ps.work_order_id
            JOIN item AS i
                ON i.item_id = wo.product_item_id
            WHERE ps.serial_no = ?
            """,
            (serial_no,),
        ).fetchone()

        if product_serial is None:
            raise ValueError(
                f"Serial 번호를 찾을 수 없습니다: {serial_no}"
            )

        if product_serial["serial_status"] != "IN_PROGRESS":
            raise ValueError(
                "EOL 검사를 등록할 수 없는 Serial 상태입니다: "
                f"{product_serial['serial_status']}"
            )

        # 센서형 제품은 각도 측정값 필수
        if product_serial["product_code"] == "ACT-SENSOR":
            if (
                target_angle_deg is None
                or actual_angle_deg is None
            ):
                raise ValueError(
                    "센서형 제품은 목표 각도와 실제 각도를 "
                    "반드시 입력해야 합니다."
                )

        # 현재 등록할 차례인 필수 공정 조회
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
                "등록할 필수 공정이 없습니다. "
                "모든 필수 공정이 이미 등록되었는지 확인하세요."
            )

        if next_routing_step["process_code"] != "PROC-EOL":
            raise ValueError(
                "현재 등록해야 할 공정은 "
                f"{next_routing_step['process_code']}"
                f"({next_routing_step['process_name']})입니다."
            )

        # -------------------------
        # 5. process_history 저장
        # -------------------------
        process_cursor = connection.execute(
            """
            INSERT INTO process_history(
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
                product_serial["product_serial_id"],
                next_routing_step["routing_step_id"],
                result,
                failure_reason,
            ),
        )

        process_history_id = process_cursor.lastrowid

        # -------------------------
        # 6. eol_test_result 저장
        # -------------------------
        eol_cursor = connection.execute(
            """
            INSERT INTO eol_test_result(
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
                float(max_current_ma),
                target_angle_deg,
                actual_angle_deg,
                position_error_deg,
                result,
                failure_reason,
            ),
        )

        eol_test_result_id = eol_cursor.lastrowid

        # -------------------------
        # 7. EOL FAIL인 경우 Serial 종료
        # -------------------------
        if result == "FAIL":
            connection.execute(
                """
                UPDATE product_serial
                SET
                    status = 'FAIL',
                    completed_at = datetime('now', 'localtime')
                WHERE product_serial_id = ?
                AND status = 'IN_PROGRESS'
                """,
                (product_serial["product_serial_id"],),
            )

            update_work_order_status(
                connection,
                product_serial["work_order_id"],
            )

        return {
            "process_history_id": process_history_id,
            "eol_test_result_id": eol_test_result_id,
            "result": result,
            "position_error_deg": position_error_deg,
            "failure_reason": failure_reason,
        }


def complete_production(serial_no: str) -> dict:
    """
    모든 선행 필수 공정이 PASS인지 확인한 뒤,
    생산 완료 공정(PROC-COMPLETE)을 등록하고
    Serial을 최종 PASS 상태로 변경한다.
    """

    # -------------------------
    # 1. 입력값 검증
    # -------------------------
    if not isinstance(serial_no, str):
        raise ValueError("Serial 번호는 문자열이어야 합니다.")

    serial_no = serial_no.strip()

    if not serial_no:
        raise ValueError("Serial 번호를 입력하세요.")

    with get_connection() as connection:
        # -------------------------
        # 2. Serial 및 제품 정보 조회
        # -------------------------
        product_serial = connection.execute(
            """
            SELECT
                ps.product_serial_id,
                ps.serial_no,
                ps.status AS serial_status,
                ps.work_order_id,
                wo.product_item_id,
                i.item_code AS product_code,
                i.item_name AS product_name
            FROM product_serial AS ps
            JOIN work_order AS wo
                ON wo.work_order_id = ps.work_order_id
            JOIN item AS i
                ON i.item_id = wo.product_item_id
            WHERE ps.serial_no = ?
            """,
            (serial_no,),
        ).fetchone()

        if product_serial is None:
            raise ValueError(
                f"Serial 번호를 찾을 수 없습니다: {serial_no}"
            )

        if product_serial["serial_status"] != "IN_PROGRESS":
            raise ValueError(
                "생산 완료 처리할 수 없는 Serial 상태입니다: "
                f"{product_serial['serial_status']}"
            )

        # -------------------------
        # 3. 생산 완료 공정 조회
        # -------------------------
        completion_step = connection.execute(
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
              AND p.process_code = 'PROC-COMPLETE'
            """,
            (product_serial["product_item_id"],),
        ).fetchone()

        if completion_step is None:
            raise ValueError(
                "제품 라우팅에서 생산 완료 공정을 "
                "찾을 수 없습니다."
            )

        # -------------------------
        # 4. 생산 완료 이력 중복 확인
        # -------------------------
        existing_completion = connection.execute(
            """
            SELECT
                process_history_id,
                result
            FROM process_history
            WHERE product_serial_id = ?
              AND routing_step_id = ?
            """,
            (
                product_serial["product_serial_id"],
                completion_step["routing_step_id"],
            ),
        ).fetchone()

        if existing_completion is not None:
            raise ValueError(
                "생산 완료 공정이 이미 등록되어 있습니다."
            )

        # -------------------------
        # 5. 선행 필수 공정 검증
        # -------------------------
        incomplete_step = connection.execute(
            """
            SELECT
                rs.sequence_no,
                p.process_code,
                p.process_name,
                ph.result
            FROM routing_step AS rs
            JOIN process AS p
                ON p.process_id = rs.process_id
            LEFT JOIN process_history AS ph
                ON ph.product_serial_id = ?
               AND ph.routing_step_id = rs.routing_step_id
            WHERE rs.product_item_id = ?
              AND rs.is_active = 1
              AND rs.is_required = 1
              AND rs.sequence_no < ?
              AND (
                    ph.process_history_id IS NULL
                    OR ph.result != 'PASS'
              )
            ORDER BY rs.sequence_no
            LIMIT 1
            """,
            (
                product_serial["product_serial_id"],
                product_serial["product_item_id"],
                completion_step["sequence_no"],
            ),
        ).fetchone()

        if incomplete_step is not None:
            step_status = (
                incomplete_step["result"]
                if incomplete_step["result"] is not None
                else "미등록"
            )

            raise ValueError(
                "생산 완료 전 선행 공정을 확인하세요: "
                f"{incomplete_step['process_code']} "
                f"({incomplete_step['process_name']}, "
                f"{step_status})"
            )

        # -------------------------
        # 6. 생산 완료 공정 이력 저장
        # -------------------------
        process_cursor = connection.execute(
            """
            INSERT INTO process_history(
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
                ?
            )
            """,
            (
                product_serial["product_serial_id"],
                completion_step["routing_step_id"],
                "모든 필수 공정 완료",
            ),
        )

        process_history_id = process_cursor.lastrowid

        # -------------------------
        # 7. Serial 최종 PASS 처리
        # -------------------------
        serial_cursor = connection.execute(
            """
            UPDATE product_serial
            SET
                status = 'PASS',
                completed_at = datetime('now', 'localtime')
            WHERE product_serial_id = ?
              AND status = 'IN_PROGRESS'
            """,
            (product_serial["product_serial_id"],),
        )

        if serial_cursor.rowcount != 1:
            raise ValueError(
                "Serial 상태가 변경되어 생산 완료 처리에 실패했습니다."
            )

        update_work_order_status(
            connection,
            product_serial["work_order_id"],
        )

        return {
            "product_serial_id": (
                product_serial["product_serial_id"]
            ),
            "serial_no": product_serial["serial_no"],
            "work_order_id": product_serial["work_order_id"],
            "process_history_id": process_history_id,
            "process_code": completion_step["process_code"],
            "process_name": completion_step["process_name"],
            "result": "PASS",
            "serial_status": "PASS",
        }
