from src.third_material_service import get_material_lot_inventory
# EOL 결과 판정부터 DB 저장 까지

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

except ValueError as error:
    print("EOL 검사 판정 실패:", error)

---------------------------------------------------
SQL

SELECT
    ps.serial_no,
    ps.status,
    ps.completed_at,
    ph.process_history_id,
    ph.result AS process_result,
    etr.eol_test_result_id,
    etr.forward_ok,
    etr.reverse_ok,
    etr.forward_time_ms,
    etr.reverse_time_ms,
    etr.max_current_ma,
    etr.target_angle_deg,
    etr.actual_angle_deg,
    ROUND(etr.position_error_deg, 2) AS position_error_deg,
    etr.result AS eol_result,
    etr.failure_reason,
    etr.tested_at
FROM product_serial AS ps
JOIN process_history AS ph
    ON ph.product_serial_id = ps.product_serial_id
JOIN eol_test_result AS etr
    ON etr.process_history_id = ph.process_history_id
WHERE ps.serial_no = 'WO-20260729-002-S002';
