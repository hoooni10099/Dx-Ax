
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

def update_work_order_status(
    connection,
    work_order_id: int,
) -> None:
    """
    계획수량만큼 Serial의 PASS/FAIL 결과가 확정되면
    작업지시를 COMPLETED로 변경한다.
    """

    work_order = connection.execute(
        """
        SELECT
            planned_qty,
            status
        FROM work_order
        WHERE work_order_id = ?
        """,
        (work_order_id,),
    ).fetchone()

    if work_order is None:
        raise ValueError(
            f"작업지시를 찾을 수 없습니다: {work_order_id}"
        )

    if work_order["status"] == "CANCELLED":
        return

    result_count = connection.execute(
        """
        SELECT COUNT(*) AS result_count
        FROM product_serial
        WHERE work_order_id = ?
          AND status IN ('PASS', 'FAIL')
        """,
        (work_order_id,),
    ).fetchone()["result_count"]

    if result_count >= work_order["planned_qty"]:
        connection.execute(
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
