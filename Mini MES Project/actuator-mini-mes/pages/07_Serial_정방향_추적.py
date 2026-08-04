from __future__ import annotations

import streamlit as st

from src.traceability_service import (
    get_serial_eol_result,
    get_serial_material_trace,
    get_serial_options,
    get_serial_process_history,
    get_serial_summary,
)
from src.ui import page_title, setup_page


setup_page("Serial 추적")

page_title(
    title="Serial 정방향 추적",
)

st.divider()

serial_options_dataframe = get_serial_options()

if serial_options_dataframe.empty:
    st.info("추적할 Serial이 없습니다.")

else:
    serial_option_map = dict(
        zip(
            serial_options_dataframe["serial_no"],
            serial_options_dataframe["product_serial_id"],
        )
    )

    selected_serial_no = st.selectbox(
        "추적할 Serial",
        options=list(serial_option_map.keys()),
    )

    selected_product_serial_id = serial_option_map[
        selected_serial_no
    ]

    serial_summary = get_serial_summary(
        selected_product_serial_id
    )

    if serial_summary.empty:
        st.warning("선택한 Serial의 기본정보를 찾을 수 없습니다.")

    else:
        summary = serial_summary.iloc[0]

        st.subheader("완제품 정보")

        column1, column2, column3, column4 = st.columns(4)

        with column1:
            st.metric("Serial 번호", summary["serial_no"])

        with column2:
            st.metric("제품 코드", summary["item_code"])

        with column3:
            st.metric("Serial 상태", summary["serial_status"])

        with column4:
            st.metric("작업지시", summary["work_order_no"])

        summary_display = serial_summary.rename(
            columns={
                "serial_no": "Serial 번호",
                "item_code": "제품 코드",
                "item_name": "제품명",
                "serial_status": "Serial 상태",
                "work_order_no": "작업지시 번호",
                "work_order_status": "작업지시 상태",
                "planned_qty": "계획 수량",
                "due_date": "납기일",
                "serial_started_at": "생산 시작 시각",
                "serial_completed_at": "생산 완료 시각",
            }
        )

        st.dataframe(
            summary_display[
                [
                    "Serial 번호",
                    "제품 코드",
                    "제품명",
                    "Serial 상태",
                    "작업지시 번호",
                    "작업지시 상태",
                    "계획 수량",
                    "납기일",
                    "생산 시작 시각",
                    "생산 완료 시각",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("투입 자재 LOT")

        material_trace = get_serial_material_trace(
            selected_product_serial_id
        )

        if material_trace.empty:
            st.info(
                "이 Serial에 등록된 자재 투입 이력이 없습니다."
            )

        else:
            material_display = material_trace.rename(
                columns={
                    "sequence_no": "공정 순서",
                    "process_code": "공정 코드",
                    "process_name": "투입 공정",
                    "material_code": "자재 코드",
                    "material_name": "자재명",
                    "lot_no": "자재 LOT",
                    "consumed_qty": "투입 수량",
                    "consumed_at": "투입 시각",
                    "received_date": "입고일",
                    "lot_status": "LOT 상태",
                }
            )

            st.dataframe(
                material_display[
                    [
                        "공정 순서",
                        "투입 공정",
                        "자재 코드",
                        "자재명",
                        "자재 LOT",
                        "투입 수량",
                        "투입 시각",
                        "입고일",
                        "LOT 상태",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )
        st.divider()
        st.subheader("공정 작업 이력")

        process_history = get_serial_process_history(
            selected_product_serial_id
        )

        if process_history.empty:
            st.info(
                "이 Serial에 등록된 공정 작업 이력이 없습니다."
            )

        else:
            process_history_display = process_history.copy()

            process_history_display["is_required"] = (
                process_history_display["is_required"].map(
                    {
                        1: "필수",
                        0: "선택",
                    }
                )
            )

            process_history_display = (
                process_history_display.rename(
                    columns={
                        "sequence_no": "공정 순서",
                        "process_code": "공정 코드",
                        "process_name": "공정명",
                        "process_type": "공정 유형",
                        "is_required": "필수 여부",
                        "result": "처리 결과",
                        "started_at": "시작 시각",
                        "completed_at": "완료 시각",
                        "remark": "비고",
                    }
                )
            )

            st.dataframe(
                process_history_display[
                    [
                        "공정 순서",
                        "공정 코드",
                        "공정명",
                        "공정 유형",
                        "필수 여부",
                        "처리 결과",
                        "시작 시각",
                        "완료 시각",
                        "비고",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        st.subheader("EOL 성능 검사 결과")

        eol_result = get_serial_eol_result(
            selected_product_serial_id
        )

        if eol_result.empty:
            st.info(
                "이 Serial에 등록된 EOL 검사 결과가 없습니다."
            )

        else:
            latest_eol = eol_result.iloc[0]

            result_column, forward_column, reverse_column = (
                st.columns(3)
            )

            with result_column:
                st.metric(
                    "최종 검사 결과",
                    latest_eol["result"],
                )

            with forward_column:
                st.metric(
                    "정방향 동작",
                    (
                        "정상"
                        if latest_eol["forward_ok"] == 1
                        else "이상"
                    ),
                )

            with reverse_column:
                st.metric(
                    "역방향 동작",
                    (
                        "정상"
                        if latest_eol["reverse_ok"] == 1
                        else "이상"
                    ),
                )

            eol_display = eol_result.copy()

            eol_display["forward_ok"] = (
                eol_display["forward_ok"].map(
                    {
                        1: "정상",
                        0: "이상",
                    }
                )
            )

            eol_display["reverse_ok"] = (
                eol_display["reverse_ok"].map(
                    {
                        1: "정상",
                        0: "이상",
                    }
                )
            )

            eol_display = eol_display.rename(
                columns={
                    "process_name": "검사 공정",
                    "forward_ok": "정방향 동작",
                    "reverse_ok": "역방향 동작",
                    "forward_time_ms": "정방향 시간(ms)",
                    "reverse_time_ms": "역방향 시간(ms)",
                    "max_current_ma": "최대 전류(mA)",
                    "target_angle_deg": "목표 각도(°)",
                    "actual_angle_deg": "실제 각도(°)",
                    "position_error_deg": "위치 오차(°)",
                    "result": "검사 결과",
                    "failure_reason": "불합격 사유",
                    "tested_at": "검사 시각",
                }
            )

            st.dataframe(
                eol_display[
                    [
                        "검사 공정",
                        "정방향 동작",
                        "역방향 동작",
                        "정방향 시간(ms)",
                        "역방향 시간(ms)",
                        "최대 전류(mA)",
                        "목표 각도(°)",
                        "실제 각도(°)",
                        "위치 오차(°)",
                        "검사 결과",
                        "불합격 사유",
                        "검사 시각",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )
