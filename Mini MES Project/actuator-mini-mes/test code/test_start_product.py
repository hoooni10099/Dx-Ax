from src.services import start_product_serial


try:
    start_product_serial(
        serial_no="WO-20260729-002-S001"
    )

    print("제품 생산을 시작했습니다.")
    print("Serial 번호: WO-20260729-002-S001")

except ValueError as error:
    print("생산 시작 실패:", error)
