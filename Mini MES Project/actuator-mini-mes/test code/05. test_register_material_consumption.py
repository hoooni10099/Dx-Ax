# 테스트 전에 LOT 번호 확인 (Material LOT 데이터 들어가 있어야 함.)

SELECT
    ml.lot_no,
    i.item_code,
    i.item_name,
    ml.received_qty,
    ml.status
FROM material_lot AS ml
JOIN item AS i
    ON i.item_id = ml.material_item_id
WHERE i.item_code IN ('MAT-MOTOR', 'MAT-HOUSING')
ORDER BY ml.material_lot_id;

--------------------------------------------------------
# 아래 테스트 코드의 LOT 번호는 실제 DB에 저장된 번호에 맞게 바꿔야 함.

from src.services import register_material_consumption


serial_no = "WO-20260729-002-S001"

materials = [
    {
        "process_code": "PROC-MOTOR",
        "lot_no": "LOT-MOTOR-001",
        "consumed_qty": 1,
    },
    {
        "process_code": "PROC-MOTOR",
        "lot_no": "LOT-HOUSING-001",
        "consumed_qty": 1,
    },
]


for material in materials:
    try:
        consumption_id = register_material_consumption(
            serial_no=serial_no,
            process_code=material["process_code"],
            lot_no=material["lot_no"],
            consumed_qty=material["consumed_qty"],
        )

        print("자재 LOT 투입을 등록했습니다.")
        print("소비 이력 ID:", consumption_id)
        print("LOT 번호:", material["lot_no"])
        print("소비수량:", material["consumed_qty"])
        print()

    except ValueError as error:
        print(
            f"자재 LOT 투입 실패 "
            f"({material['lot_no']}): {error}"
        )


---------------------------------------------------
SQL

SELECT
    ps.serial_no,
    p.process_code,
    p.process_name,
    i.item_code AS material_code,
    i.item_name AS material_name,
    ml.lot_no,
    mc.consumed_qty,
    mc.consumed_at
FROM material_consumption AS mc
JOIN product_serial AS ps
    ON ps.product_serial_id = mc.product_serial_id
JOIN material_lot AS ml
    ON ml.material_lot_id = mc.material_lot_id
JOIN item AS i
    ON i.item_id = ml.material_item_id
JOIN routing_step AS rs
    ON rs.routing_step_id = mc.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
WHERE ps.serial_no = 'WO-20260729-002-S001'
ORDER BY mc.consumption_id;
