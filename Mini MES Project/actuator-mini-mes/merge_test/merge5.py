from src.db import get_connection

with get_connection() as connection:
    rows = connection.execute(
        """
        SELECT
            ml.material_lot_id,
            ml.lot_no,
            i.item_code,
            ml.received_qty,
            COALESCE(SUM(mc.consumed_qty), 0) AS consumed_qty,
            ml.received_qty
                - COALESCE(SUM(mc.consumed_qty), 0) AS remaining_qty,
            ml.status
        FROM material_lot AS ml
        JOIN item AS i
            ON i.item_id = ml.material_item_id
        LEFT JOIN material_consumption AS mc
            ON mc.material_lot_id = ml.material_lot_id
        GROUP BY
            ml.material_lot_id,
            ml.lot_no,
            i.item_code,
            ml.received_qty,
            ml.status
        ORDER BY i.item_code, ml.lot_no
        """
    ).fetchall()

for row in rows:
    print(dict(row))
