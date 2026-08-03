from __future__ import annotations

import streamlit as st

from src.process_service import (
    complete_product,
    get_completion_ready_serials,
    get_eol_ready_serials,
    register_eol_test_result,
)
from src.ui import page_title, setup_page, show_database_status


setup_page("EOL 검사 및 생산 완료")

page_title(
    title="EOL 검사 및 생산 완료",
    description=(
        "일반 공정을 모두 통과한 제품의 EOL 검사 결과를 등록하고, "
        "검사를 통과한 제품의 생산을 완료합니다."
    ),
    tables=(
        "product_serial, work_order, routing_step, process_history, "
        "eol_test_result"
    ),
    task="EOL 검사 결과 등록 및 최종 생산 완료 처리",
)

show_database_status()

st.subheader("1. EOL 검사 결과 등록")
if "eol_success_message" in st.session_state:
    st.success(
        st.session_state.pop("eol_success_message")
    )

eol_ready_serials = get_eol_ready_serials()

if eol_ready_serials.empty:
    st.info("현재 EOL 검사를 등록할 수 있는 제품 Serial이 없습니다.")

else:
    # Serial 선택 코드
    # EOL 검사 입력 폼
    serial_options = {
        (
            f"{row['serial_no']} | "
            f"{row['item_code']} | "
            f"{row['work_order_no']}"
        ): index
        for index, row in eol_ready_serials.iterrows()
    }

    selected_serial_label = st.selectbox(
        "EOL 검사 대상 Serial",
        options=list(serial_options.keys()),
    )

    selected_index = serial_options[selected_serial_label]
    selected_serial = eol_ready_serials.loc[selected_index]

    column1, column2, column3 = st.columns(3)

    with column1:
        st.metric(
            "Serial Number",
            selected_serial["serial_no"],
        )

    with column2:
        st.metric(
            "제품",
            selected_serial["item_name"],
        )

    with column3:
        st.metric(
            "작업지시",
            selected_serial["work_order_no"],
        )

    st.write(eol_ready_serials.columns.tolist())
    st.dataframe(eol_ready_serials)

    is_sensor_product = (
        selected_serial["item_code"] == "ACT-SENSOR"
    )

    with st.form("eol_test_form"):
        st.markdown("#### 동작 검사")

        column1, column2 = st.columns(2)

        with column1:
            forward_ok = st.checkbox(
                "정방향 동작 정상",
                value=True,
            )

            forward_time_ms = st.number_input(
                "정방향 동작시간(ms)",
                min_value=0,
                step=1,
            )

        with column2:
            reverse_ok = st.checkbox(
                "역방향 동작 정상",
                value=True,
            )

            reverse_time_ms = st.number_input(
                "역방향 동작시간(ms)",
                min_value=0,
                step=1,
            )

        max_current_ma = st.number_input(
            "최대 전류(mA)",
            min_value=0.0,
            step=10.0,
        )

        target_angle_deg = None
        actual_angle_deg = None

        if is_sensor_product:
            st.markdown("#### 위치센서 검사")

            column1, column2 = st.columns(2)

            with column1:
                target_angle_deg = st.number_input(
                    "목표 각도(°)",
                    min_value=0.0,
                    max_value=360.0,
                    step=0.1,
                )

            with column2:
                actual_angle_deg = st.number_input(
                    "실제 각도(°)",
                    min_value=0.0,
                    max_value=360.0,
                    step=0.1,
                )

            position_error_deg = abs(
                actual_angle_deg - target_angle_deg
            )

            st.metric(
                "위치 오차",
                f"{position_error_deg:.1f}°",
            )

        else:
            position_error_deg = None
            st.info(
                "ACT-BASIC 제품은 위치센서 검사 대상이 아닙니다."
            )

        st.markdown("#### 최종 판정")

        st.info(
            "PASS/FAIL은 입력한 측정값을 기준으로 자동 판정됩니다."
        )

        submitted = st.form_submit_button(
            "EOL 검사 결과 등록",
            type="primary",
        )

    if submitted:
        try:
            result, failure_reason = register_eol_test_result(
                product_serial_id=int(
                    selected_serial["product_serial_id"]
                ),
                routing_step_id=int(
                    selected_serial["routing_step_id"]
                ),
                forward_ok=forward_ok,
                reverse_ok=reverse_ok,
                forward_time_ms=int(forward_time_ms),
                reverse_time_ms=int(reverse_time_ms),
                max_current_ma=float(max_current_ma),
                target_angle_deg=(
                    float(target_angle_deg)
                    if target_angle_deg is not None
                    else None
                ),
                actual_angle_deg=(
                    float(actual_angle_deg)
                    if actual_angle_deg is not None
                    else None
                ),
            )

            if result == "PASS":
                st.session_state["eol_success_message"] = (
                    "EOL 검사를 통과했습니다. "
                    "이제 생산 완료 처리가 가능합니다."
                )
            else:
                message = "EOL 검사 결과가 FAIL로 등록되었습니다."

                if failure_reason:
                    message += f" 불합격 사유: {failure_reason}"

                st.session_state["eol_success_message"] = message

            st.rerun()

        except ValueError as error:
            st.error(str(error))

        except Exception as error:
            st.error(
                f"EOL 검사 결과 등록 중 오류가 발생했습니다: {error}"
            )

st.divider()

st.subheader("2. 생산 완료 처리")

if "completion_success_message" in st.session_state:
    st.success(
        st.session_state.pop("completion_success_message")
    )

completion_ready_serials = get_completion_ready_serials()

if completion_ready_serials.empty:
    st.info("현재 생산 완료 처리할 수 있는 제품 Serial이 없습니다.")

else:
    completion_options = {
        (
            f"{row['serial_no']} | "
            f"{row['item_code']} | "
            f"{row['work_order_no']}"
        ): index
        for index, row in completion_ready_serials.iterrows()
    }

    selected_completion_label = st.selectbox(
        "생산 완료 대상 Serial",
        options=list(completion_options.keys()),
        key="completion_serial_selectbox",
    )

    selected_completion_index = completion_options[
        selected_completion_label
    ]

    selected_completion_serial = completion_ready_serials.loc[
        selected_completion_index
    ]

    column1, column2, column3 = st.columns(3)

    with column1:
        st.metric(
            "Serial Number",
            selected_completion_serial["serial_no"],
        )

    with column2:
        st.metric(
            "제품",
            selected_completion_serial["item_name"],
        )

    with column3:
        st.metric(
            "작업지시",
            selected_completion_serial["work_order_no"],
        )

    st.info(
        "생산 완료 처리하면 해당 Serial은 최종 PASS 상태로 종료됩니다."
    )

    if st.button(
        "생산 완료 처리",
        type="primary",
        key="complete_product_button",
    ):
        try:
            complete_product(
                product_serial_id=int(
                    selected_completion_serial[
                        "product_serial_id"
                    ]
                ),
                routing_step_id=int(
                    selected_completion_serial[
                        "routing_step_id"
                    ]
                ),
            )

            st.session_state["completion_success_message"] = (
                f"{selected_completion_serial['serial_no']}의 "
                "생산 완료 처리가 정상적으로 등록되었습니다."
            )

            st.rerun()

        except ValueError as error:
            st.error(str(error))

        except Exception as error:
            st.error(
                f"생산 완료 처리 중 오류가 발생했습니다: {error}"
            )
