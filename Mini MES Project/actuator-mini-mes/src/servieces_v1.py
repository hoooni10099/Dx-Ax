from src.db import get_connection

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
