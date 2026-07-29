from src.services import register_process_result


try:
    process_history_id = register_process_result(
        serial_no="WO-20260729-002-S001",
        process_code="PROC-MOTOR",
        result="PASS",
        remark="모터 조립 정상 완료",
    )

    print("공정 실적을 등록했습니다.")
    print("공정 실적 ID:", process_history_id)
    print("Serial 번호: WO-20260729-002-S001")
    print("공정 코드: PROC-MOTOR")
    print("결과: PASS")

except ValueError as error:
    print("공정 실적 등록 실패:", error)
