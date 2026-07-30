from src.fourth_eol_service import complete_production
# EOL 검사가 이미 등록되어 있어, EOL을 다시 등록하지 말고 complete_production()만 실행

SERIAL_NO = "WO-20260730-001-S001"


try:
    completion_result = complete_production(SERIAL_NO)

    print("\n[생산 완료 결과]")
    print(
        "공정 이력 ID:",
        completion_result["process_history_id"],
    )
    print("공정 코드:", completion_result["process_code"])
    print("공정 이름:", completion_result["process_name"])
    print("공정 결과:", completion_result["result"])
    print("Serial 상태:", completion_result["serial_status"])

except ValueError as error:
    print("\n생산 완료 처리 실패:", error)
