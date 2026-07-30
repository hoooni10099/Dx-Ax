from src.fifth_tracking_service import (
    get_serial_summary,
    get_serial_process_status,
    get_serial_material_trace,
    get_serial_eol_result,
    get_material_lot_usage,)

serial_numbers = [
    "WO-20260730-001-S001",
    "존재하지않는-SERIAL",
    "   ",
]

# Serial 요약 조회 테스트
for serial_no in serial_numbers:
    try:
        summary = get_serial_summary(serial_no)

        print(f"\nSerial 조회: {serial_no}")
        for key, value in summary.items():
            print(f"{key}: {value}")

    except ValueError as error:
        print(f"\n조회 실패 ({serial_no!r}): {error}")

# Serial별 공정 상세 현황 조회 테스트
try:
    processes = get_serial_process_status(
        "WO-20260730-001-S001"
    )

    print("\n공정 상세 현황")
    for process in processes:
        print(process)

except ValueError as error:
    print("공정 현황 조회 실패:", error)

try:
    materials = get_serial_material_trace(
        "WO-20260730-001-S001"
    )

    print("\nSerial별 자재 LOT 투입 이력")

    if not materials:
        print("등록된 자재 투입 이력이 없습니다.")
    else:
        for material in materials:
            print(material)

except ValueError as error:
    print("자재 LOT 추적 실패:", error)

try:
    eol_result = get_serial_eol_result(
        "WO-20260730-001-S001"
    )

    print("\nEOL 성능 검사 상세 결과")

    if eol_result is None:
        print("등록된 EOL 검사 실적이 없습니다.")
    else:
        for key, value in eol_result.items():
            print(f"{key}: {value}")

except ValueError as error:
    print("EOL 검사 결과 조회 실패:", error)

try:
    usages = get_material_lot_usage(
        "LOT-MOTOR-20260701-A"
    )

    print("\n자재 LOT 사용처 역추적 결과")

    if not usages:
        print("아직 이 LOT를 사용한 생산 이력이 없습니다.")
    else:
        for usage in usages:
            print(usage)

except ValueError as error:
    print("자재 LOT 역추적 실패:", error)
