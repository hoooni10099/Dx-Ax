from src.fifth_tracking_service import (
    get_serial_summary,
    get_serial_process_status,
    get_serial_material_trace,
    get_serial_eol_result,
    get_material_lot_usage,
    get_material_lot_summary,
)


PASS_SERIAL = "WO-20260730-001-S001"
FAIL_SERIAL = "WO-20260730-001-S002"
VALID_LOT = "LOT-MOTOR-20260715-B"


def print_title(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_serial_summary():
    print_title("1. Serial 생산 진행 요약")

    for serial_no in [
        PASS_SERIAL,
        FAIL_SERIAL,
        "WO-20260730-001-S001",
    ]:
        try:
            result = get_serial_summary(serial_no)
            print(f"\n조회 성공: {serial_no}")

            for key, value in result.items():
                print(f"{key}: {value}")

        except ValueError as error:
            print(f"\n조회 실패 ({serial_no!r}): {error}")


def test_serial_process_status():
    print_title("2. Serial별 전체 공정 상태")

    for serial_no in [PASS_SERIAL, FAIL_SERIAL]:
        try:
            processes = get_serial_process_status(serial_no)
            print(f"\nSerial: {serial_no}")

            for process in processes:
                print(
                    process["sequence_no"],
                    process["process_code"],
                    process["process_name"],
                    process["display_status"],
                )

        except ValueError as error:
            print("공정 현황 조회 실패:", error)


def test_serial_material_trace():
    print_title("3. Serial별 자재 LOT 투입 이력")

    try:
        materials = get_serial_material_trace(FAIL_SERIAL)

        if not materials:
            print("등록된 자재 투입 이력이 없습니다.")
        else:
            for material in materials:
                print(material)

    except ValueError as error:
        print("자재 LOT 추적 실패:", error)


def test_serial_eol_result():
    print_title("4. Serial EOL 검사 상세 결과")

    try:
        result = get_serial_eol_result(FAIL_SERIAL)

        if result is None:
            print("등록된 EOL 검사 실적이 없습니다.")
            return

        for key, value in result.items():
            if key == "position_error_deg" and value is not None:
                print(f"{key}: {value:.2f}°")
            else:
                print(f"{key}: {value}")

    except ValueError as error:
        print("EOL 검사 결과 조회 실패:", error)


def test_material_lot_usage():
    print_title("5. 자재 LOT 사용처 역추적")

    try:
        usages = get_material_lot_usage(VALID_LOT)

        if not usages:
            print("아직 이 LOT를 사용한 생산 이력이 없습니다.")
        else:
            for usage in usages:
                print(usage)

    except ValueError as error:
        print("자재 LOT 역추적 실패:", error)


def test_material_lot_summary():
    print_title("6. 자재 LOT 요약")

    for lot_no in [
        VALID_LOT,
        "LOT-HOUSING-20260715-B",
    ]:
        try:
            summary = get_material_lot_summary(lot_no)
            print(f"\n조회 성공: {lot_no}")

            for key, value in summary.items():
                print(f"{key}: {value}")

        except ValueError as error:
            print(f"\n조회 실패 ({lot_no!r}): {error}")


def main():
    test_serial_summary()
    test_serial_process_status()
    test_serial_material_trace()
    test_serial_eol_result()
    test_material_lot_usage()
    test_material_lot_summary()


if __name__ == "__main__":
    main()
