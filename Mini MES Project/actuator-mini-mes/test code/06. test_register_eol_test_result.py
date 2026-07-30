from src.services import register_eol_test_result
# EOL 입력값 검증과 자동 판정 로직

try:
    eol_result = register_eol_test_result(
        serial_no="WO-20260729-002-S002",
        forward_ok=True,
        reverse_ok=True,
        forward_time_ms=850,
        reverse_time_ms=900,
        max_current_ma=1200.0,
        target_angle_deg=90.0,
        actual_angle_deg=89.2,
    )

    print("EOL 검사 판정을 완료했습니다.")
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

except ValueError as error:
    print("EOL 검사 판정 실패:", error)
