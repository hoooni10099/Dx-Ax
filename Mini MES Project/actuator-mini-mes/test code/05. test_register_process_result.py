from src.third_material_service import register_process_result
# 모터, 하우징 제외
# 기어, 센서, PCB VISUAL ONLY PASS 등록

try:
    process_history_id = register_process_result(
        serial_no="WO-20260729-002-S002",
        process_code="PROC-VISUAL",
        result="PASS",
        remark="외관 이상 없음",
    )

    print("공정 실적을 등록했습니다.")
    print("공정 이력 ID:", process_history_id)

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


-------------------------------------------------

SELECT
    ps.serial_no,
    rs.sequence_no,
    p.process_code,
    p.process_name,
    ph.result,
    ph.remark,
    ph.completed_at
FROM process_history AS ph
JOIN product_serial AS ps
    ON ps.product_serial_id = ph.product_serial_id
JOIN routing_step AS rs
    ON rs.routing_step_id = ph.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
WHERE ps.serial_no = 'WO-20260729-002-S001'
ORDER BY rs.sequence_no;
