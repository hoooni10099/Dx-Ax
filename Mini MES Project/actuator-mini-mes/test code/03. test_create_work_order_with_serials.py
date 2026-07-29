from src.services import create_work_order_with_serials


try:
    work_order_id, serial_numbers = create_work_order_with_serials(
        work_order_no="WO-20260729-002",
        product_item_code="ACT-SENSOR",
        planned_qty=2,
        due_date="2026-08-10",
    )

    print("생성된 작업지시 ID:", work_order_id)
    print("생성된 Serial 번호:")

    for serial_no in serial_numbers:
        print(serial_no)

except ValueError as error:
    print("작업지시 생성 실패:", error)




-------------------------------------------------------

SQL


SELECT
    wo.work_order_id,
    wo.work_order_no,
    i.item_code,
    wo.planned_qty,
    wo.status AS work_order_status,
    ps.serial_no,
    ps.status AS serial_status
FROM work_order AS wo
JOIN item AS i
    ON i.item_id = wo.product_item_id
LEFT JOIN product_serial AS ps
    ON ps.work_order_id = wo.work_order_id
ORDER BY
    wo.work_order_id,
    ps.product_serial_id;
