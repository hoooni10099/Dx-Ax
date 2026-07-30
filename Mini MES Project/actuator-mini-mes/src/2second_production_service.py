from src.db import get_connection

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
                f"{product_serial['serial_status']}"
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
