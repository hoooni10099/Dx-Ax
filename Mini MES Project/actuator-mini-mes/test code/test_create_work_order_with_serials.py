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
