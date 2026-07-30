from src.fourth_eol_service import (
    register_eol_test_result,
    complete_production,
)


SERIAL_NO = "새로운-IN_PROGRESS-SERIAL"


try:
    # 1. EOL 검사 결과 등록
    eol_result = register_eol_test_result(
        serial_no=SERIAL_NO,
        forward_ok=True,
        reverse_ok=True,
        forward_time_ms=890,
        reverse_time_ms=970,
        max_current_ma=1100.0,
        target_angle_deg=85.0,
        actual_angle_deg=85.8,
    )

    print("\n[EOL 검사 결과]")
    print("공정 이력 ID:", eol_result["process_history_id"])
    print("EOL 검사 결과 ID:", eol_result["eol_test_result_id"])
    print("판정:", eol_result["result"])

    position_error = eol_result["position_error_deg"]

    if position_error is None:
        print("위치 오차: 측정 안 함")
    else:
        print(f"위치 오차: {position_error:.2f}도")

    print(
        "실패 사유:",
        eol_result["failure_reason"] or "없음",
    )

    # 2. EOL PASS일 때만 생산 완료 처리
    if eol_result["result"] == "PASS":
        completion_result = complete_production(SERIAL_NO)

        print("\n[생산 완료 결과]")
        print(
            "생산 완료 공정 이력 ID:",
            completion_result["process_history_id"],
        )
        print("공정 코드:", completion_result["process_code"])
        print("공정 결과:", completion_result["result"])
        print("Serial 상태:", completion_result["serial_status"])

    else:
        print("\nEOL 검사에 실패하여 생산 완료 처리를 진행하지 않습니다.")

except ValueError as error:
    print("\n처리 실패:", error)
