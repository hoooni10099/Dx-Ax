from __future__ import annotations

import pandas as pd

from src.db import get_connection


def get_items(
    item_type: str | None = None,
    is_active: int | None = None,
    keyword: str | None = None,
) -> pd.DataFrame:
    sql = """
        SELECT
            item_code AS "품목코드",
            item_name AS "품목명",
            item_type AS "품목유형",
            CASE is_active
                WHEN 1 THEN '사용'
                ELSE '미사용'
            END AS "사용여부"
        FROM item
        WHERE 1 = 1
    """

    params = []

    if item_type is not None:
        sql += """
            AND item_type = ?
        """
        params.append(item_type)

    if is_active is not None:
        sql += """
            AND is_active = ?
        """
        params.append(is_active)

    if keyword is not None and keyword.strip():
        sql += """
            AND (
                item_code LIKE ?
                OR item_name LIKE ?
            )
        """

        search_keyword = f"%{keyword.strip()}%"
        params.extend([search_keyword, search_keyword])

    sql += """
        ORDER BY
            CASE item_type
                WHEN 'PRODUCT' THEN 1
                WHEN 'MATERIAL' THEN 2
                ELSE 3
            END,
            item_code
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )

def get_products() -> pd.DataFrame:
    sql = """
        SELECT
            item_id,
            item_code,
            item_name
        FROM item
        WHERE item_type = 'PRODUCT'
          AND is_active = 1
        ORDER BY item_code
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def get_bom_by_product(product_item_id: int) -> pd.DataFrame:
    sql = """
        SELECT
            material.item_code AS "자재코드",
            material.item_name AS "자재명",
            bom.required_qty AS "소요수량",
            process.process_name AS "투입공정",
            routing_step.sequence_no AS "공정순서"
        FROM bom
        JOIN item AS material
          ON material.item_id = bom.material_item_id
        JOIN routing_step
          ON routing_step.routing_step_id = bom.input_routing_step_id
        JOIN process
          ON process.process_id = routing_step.process_id
        WHERE bom.product_item_id = ?
          AND bom.is_active = 1
          AND material.is_active = 1
          AND routing_step.is_active = 1
        ORDER BY
            routing_step.sequence_no,
            material.item_code
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=[product_item_id],
        )

def get_routing_by_product(product_item_id: int) -> pd.DataFrame:
    sql = """
        SELECT
            routing_step.sequence_no AS "공정순서",
            process.process_code AS "공정코드",
            process.process_name AS "공정명",
            CASE process.process_type
                WHEN 'ASSEMBLY' THEN '조립'
                WHEN 'INSPECTION' THEN '검사'
                WHEN 'COMPLETION' THEN '완료'
                ELSE process.process_type
            END AS "공정유형",
            CASE routing_step.is_required
                WHEN 1 THEN '필수'
                ELSE '선택'
            END AS "필수여부"
        FROM routing_step
        JOIN process
          ON process.process_id = routing_step.process_id
        WHERE routing_step.product_item_id = ?
          AND routing_step.is_active = 1
        ORDER BY routing_step.sequence_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=[product_item_id],
        )
