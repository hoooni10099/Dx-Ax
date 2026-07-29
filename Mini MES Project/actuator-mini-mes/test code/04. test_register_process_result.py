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


------------------------------------------------
SQL

SELECT
    ps.serial_no,
    rs.sequence_no,
    p.process_code,
    p.process_name,
    ph.result,
    ph.started_at,
    ph.completed_at,
    ph.remark
FROM process_history AS ph
JOIN product_serial AS ps
    ON ps.product_serial_id = ph.product_serial_id
JOIN routing_step AS rs
    ON rs.routing_step_id = ph.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
WHERE ps.serial_no = 'WO-20260729-002-S001'
ORDER BY rs.sequence_no;
