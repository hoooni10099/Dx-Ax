from src.services import start_product_serial


try:
    start_product_serial(
        serial_no="WO-20260729-002-S001"
    )

    print("제품 생산을 시작했습니다.")
    print("Serial 번호: WO-20260729-002-S001")

except ValueError as error:
    print("생산 시작 실패:", error)




---------------------------------------------
SQL

SELECT
    wo.work_order_no,
    wo.status AS work_order_status,
    wo.started_at AS work_order_started_at,
    ps.serial_no,
    ps.status AS serial_status,
    ps.started_at AS serial_started_at
FROM work_order AS wo
JOIN product_serial AS ps
    ON ps.work_order_id = wo.work_order_id
WHERE wo.work_order_id = 2
ORDER BY ps.product_serial_id;
