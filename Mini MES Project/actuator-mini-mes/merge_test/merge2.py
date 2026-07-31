from src.db import get_connection
from src.third_material_service import get_material_lot_inventory

print("===== 제품별 공정 순서 =====")

with get_connection() as connection:
    rows = connection.execute(
        """
        SELECT
            i.item_code AS product_code,
            rs.sequence_no,
            p.process_code,
            p.process_name,
            rs.is_required
        FROM routing_step AS rs
        JOIN item AS i
            ON i.item_id = rs.product_item_id
        JOIN process AS p
            ON p.process_id = rs.process_id
        WHERE rs.is_active = 1
        ORDER BY
            i.item_code,
            rs.sequence_no
        """
    ).fetchall()

    for row in rows:
        print(dict(row))

print("\n===== 자재 LOT 재고 =====")

inventory = get_material_lot_inventory()

if not inventory:
    print("등록된 자재 LOT가 없습니다.")
else:
    for row in inventory:
        print(dict(row))
