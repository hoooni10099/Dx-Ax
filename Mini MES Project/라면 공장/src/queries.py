from src.db import fetch_all, fetch_dataframe, fetch_one



def table_counts():
    return fetch_dataframe(
        """
        SELECT 'item' AS table_name, COUNT(*) AS row_count FROM item
        UNION ALL
        SELECT 'lot' AS table_name, COUNT(*) AS row_count FROM lot
        UNION ALL
        SELECT 'production' AS table_name, COUNT(*) AS row_count FROM production
        UNION ALL
        SELECT 'production_material' AS table_name, COUNT(*) AS row_count FROM production_material
        """
    )

def table_list():
    return fetch_dataframe(
        """
        SELECT name AS table_name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    )

def items(keyword: str = "", item_type: str = "전체"):
    params: list[str] = []
    where = ["1 = 1"]

    if keyword:
        where.append("(i.item_code LIKE ? OR i.item_name LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if item_type != "전체":
        where.append("i.item_type = ?")
        params.append(item_type)

    return fetch_dataframe(
        f"""
        SELECT
            i.item_id,
            i.item_code,
            i.item_name,
            i.item_type,
            i.unit,
            i.is_active,
            COUNT(DISTINCT l.lot_id) AS lot_count,
            COUNT(DISTINCT pm.production_material_id) AS material_use_count
        FROM item AS i
        LEFT JOIN lot AS l
            ON i.item_id = l.item_id
        LEFT JOIN production_material AS pm
            ON i.item_id = pm.material_item_id
        WHERE {' AND '.join(where)}
        GROUP BY
            i.item_id,
            i.item_code,
            i.item_name,
            i.item_type,
            i.unit,
            i.is_active
        ORDER BY i.item_type, i.item_code
        """,
        tuple(params),
    )

def item_type_counts():
    return fetch_dataframe(
        """
        SELECT item_type, COUNT(*) AS item_count
        FROM item
        GROUP BY item_type
        ORDER BY item_type
        """
    )

def item_name_lot(): # 품목명과 함께 LOT 재고 조회
    return fetch_dataframe(
        """
        SELECT
            i.item_name,
            l.qty,
        FROM lot as l
        JOIN item as i ON l.item_id = i.item_id
        ORDER BY i.item_code, l.lot_no;

        """
    )
