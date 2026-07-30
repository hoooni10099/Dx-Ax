from src.third_material_service import get_material_lot_inventory

inventory = get_material_lot_inventory()

for row in inventory:
    print(
        row["lot_no"],
        row["item_code"],
        "입고:", row["received_qty"],
        "투입:", row["consumed_qty"],
        "잔여:", row["remaining_qty"],
        "상태:", row["status"],
    )
