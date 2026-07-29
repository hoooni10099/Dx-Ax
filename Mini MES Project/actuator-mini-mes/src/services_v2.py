from src.db import get_connection
from datetime import datetime

# 입력한 품목 코드가 생산할 수 있는 완제품인가?
def find_active_product(product_item_code: str):
    product_item_code = product_item_code.strip()

    if not product_item_code:
        raise ValueError('제품 품목 코드를 입력해야 합니다.')

    with get_connection() as connection:
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
        (product_item_code,),
        # 값이 하나뿐이어도 뒤에 쉼표가 있어야 문자열이 아니라 SQL에
        #전달할 값이 담긴 튜플이 됨
        ).fetchone()

    if product is None:
        raise ValueError(
            f'생산 가능한 완제품 품목을 찾을 수 없습니다: {product_item_code}'
        )

    return product

# 작업지시 1건만 저장하는 함수
def create_work_order_only(
    work_order_no: str,
    product_item_code: str,
    planned_qty: int,
    due_date: str,
) -> int:
    work_order_no = work_order_no.strip()

    # 입력값이 올바른지 확인
    if not work_order_no:
        raise ValueError('작업 지시 번호를 입력해야 합니다.')

    if not isinstance(planned_qty, int) or isinstance(planned_qty, bool):
        raise ValueError('계획 수량은 정수여야 합니다.')

    if planned_qty <= 0:
        raise ValueError('계획 수량은 1 이상이어야 합니다.')

    try:
        datetime.strptime(due_date, '%Y-%m-%d')
    except ValueError as error:
        raise ValueError(
            '납기일은 YYYY-MM-DD 형식이어야 합니다.'
        ) from error

    # 생산 가능한 완제품인지 확인
    product = find_active_product(product_item_code)

    # 같은 작업 지시 번호가 이미 있는지 확인
    with get_connection() as connection:
        duplicated_order = connection.execute(
            """
            SELECT  work_order_id
            FROM work_order
            WHERE work_order_no = ?
            """,
            (work_order_no,),
        ).fetchone()

        if duplicated_order is not None:
            raise ValueError(
                f'이미 등록된 작업 지시 번호입니다 : {work_order_no}'
            )

        # work_order Table에 한 행 삽입
        cursor = connection.execute(
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
        # 새로 생성된 work_order_id 반환
        work_order_id = cursor.lastrowid

    return work_order_id
