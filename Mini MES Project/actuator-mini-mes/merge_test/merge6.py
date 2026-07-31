from src.third_material_service import register_material_consumption


TEST_CASES = [
    {
        "serial_no": "WO-20260731-INTEGRATION-02-S001",
        "expected_status": "PASS",
    },
    {
        "serial_no": "WO-20260731-INTEGRATION-02-S002",
        "expected_status": "FAIL",
    },
]


for index, test_case in enumerate(TEST_CASES, start=1):
    serial_no = test_case["serial_no"]
    expected_status = test_case["expected_status"]

    print(
        f"===== {index}. {expected_status} Serial 자재 추가 투입 ====="
    )

    try:
        register_material_consumption(
            serial_no=serial_no,
            process_code="PROC-MOTOR",
            lot_no="LOT-MOTOR-20260715-B",
            consumed_qty=1,
        )

        print(
            "테스트 실패: 생산이 종료된 Serial에 "
            "자재가 등록되었습니다."
        )

    except ValueError as error:
        print("정상 차단:", error)

    print()
