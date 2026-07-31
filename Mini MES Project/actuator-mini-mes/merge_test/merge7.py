from datetime import date, timedelta

from src.first_work_order_service import create_work_order_with_serials
from src.second_production_service import start_product_serial

from src.third_material_service import (register_material_consumption,
                                        register_process_result,)


WORK_ORDER_NO = "WO-20260731-COMPLETED-PROCESS-TEST-01"


# 1. 테스트용 작업지시와 Serial 생성
_, serial_numbers = create_work_order_with_serials(
    work_order_no=WORK_ORDER_NO,
    product_item_code="ACT-SENSOR",
    planned_qty=1,
    due_date=(date.today() + timedelta(days=7)).isoformat(),
)

serial_no = serial_numbers[0]
start_product_serial(serial_no)

print("생성된 Serial:", serial_no)


# 2. PROC-MOTOR에 필요한 BOM 자재 투입
motor_consumption_id = register_material_consumption(
    serial_no=serial_no,
    process_code="PROC-MOTOR",
    lot_no="LOT-MOTOR-20260715-B",
    consumed_qty=1,
)

housing_consumption_id = register_material_consumption(
    serial_no=serial_no,
    process_code="PROC-MOTOR",
    lot_no="LOT-HOUSING-20260715-B",
    consumed_qty=1,
)

print("모터 투입:", motor_consumption_id)
print("하우징 투입:", housing_consumption_id)


# 3. PROC-MOTOR 공정 완료
process_history_id = register_process_result(
    serial_no=serial_no,
    process_code="PROC-MOTOR",
    result="PASS",
    remark="완료 공정 자재 추가 투입 차단 테스트",
)

print("PROC-MOTOR 완료:", process_history_id)


# 4. 이미 완료된 PROC-MOTOR에 자재 추가 투입 시도
print("\n===== 완료된 공정에 자재 추가 투입 =====")

try:
    register_material_consumption(
        serial_no=serial_no,
        process_code="PROC-MOTOR",
        lot_no="LOT-MOTOR-20260701-A",
        consumed_qty=1,
    )

    print("테스트 실패: 완료된 공정에 자재가 등록되었습니다.")

except ValueError as error:
    print("정상 차단:", error)
