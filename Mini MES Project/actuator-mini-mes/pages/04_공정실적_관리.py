from __future__ import annotations

import streamlit as st
import altair as alt
import pandas as pd

from src.process_service import (
    get_history_serials,
    get_process_ready_serials,
    get_required_material_lots,
    get_serial_material_consumptions,
    get_serial_process_history,
    register_process_result,
)

from src.process_history_service import (
    get_process_performance_metrics,
    get_process_result_summary,
)

from src.ui import (
    page_title,
    setup_page,
)

def show_process_performance_metrics(metrics: dict):
    """공정실적 핵심 지표를 표시한다."""

    st.subheader("공정실적 현황")

    column1, column2, column3, column4 = st.columns(4)

    column1.metric(
        label="전체 공정실적",
        value=f"{metrics['total_history_count']:,}건",
    )

    column2.metric(
        label="합격",
        value=f"{metrics['pass_count']:,}건",
    )

    column3.metric(
        label="불합격",
        value=f"{metrics['fail_count']:,}건",
    )

    column4.metric(
        label="공정 완료율",
        value=f"{metrics['completion_rate']:.1f}%",
        help=(
            f"완료 필수 공정 {metrics['completed_process_count']:,}건 / "
            f"전체 예정 필수 공정 {metrics['expected_process_count']:,}건"
        ),
    )

def show_process_result_chart(df: pd.DataFrame):
    """공정별 합격·불합격 수량을 누적 가로 막대로 표시한다."""

    st.subheader("공정별 합격·불합격 수량")

    if df.empty:
        st.info("표시할 공정실적이 없습니다.")
        return

    process_order = (
        df[["process_name", "sequence_no"]]
        .drop_duplicates()
        .sort_values(
            by=["sequence_no", "process_name"],
            ascending=[True, True],
        )["process_name"]
        .tolist()
    )

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X(
                "result_qty:Q",
                title="실적 수량",
                axis=alt.Axis(tickMinStep=1),
                stack="zero",
            ),
            y=alt.Y(
                "process_name:N",
                title=None,
                sort=process_order,
            ),
            color=alt.Color(
                "result_name:N",
                title="판정 결과",
                scale=alt.Scale(
                    domain=["합격", "불합격"],
                    range=["#16A34A", "#DC2626"],
                ),
            ),
            order=alt.Order(
                "result:N",
                sort="descending",
            ),
            tooltip=[
                alt.Tooltip(
                    "process_code:N",
                    title="공정 코드",
                ),
                alt.Tooltip(
                    "process_name:N",
                    title="공정명",
                ),
                alt.Tooltip(
                    "sequence_no:Q",
                    title="공정 순서",
                    format="d",
                ),
                alt.Tooltip(
                    "result_name:N",
                    title="판정",
                ),
                alt.Tooltip(
                    "result_qty:Q",
                    title="수량",
                    format=",d",
                ),
            ],
        )
        .properties(height=320)
    )

    st.altair_chart(
        chart,
        width="stretch",
    )

def show_process_performance_summary():
    """공정실적 핵심 지표와 결과 차트를 표시한다."""

    metrics = get_process_performance_metrics()
    result_df = get_process_result_summary()

    show_process_performance_metrics(metrics)
    show_process_result_chart(result_df)


setup_page("공정실적 관리")

page_title(
    title="공정실적 관리",
)

st.divider()

show_process_performance_summary()

st.divider()

st.subheader("공정 투입 대상 선택")

if "process_success_message" in st.session_state:
    st.success(
        st.session_state.pop("process_success_message")
    )

ready_serials = get_process_ready_serials()

if ready_serials.empty:
    st.info("현재 공정 실적을 등록할 수 있는 Serial이 없습니다.")
else:
    serial_records = ready_serials.to_dict(orient="records")

    serial_options = {
        (
            f"{row['serial_no']} | "
            f"{row['process_code']} - {row['process_name']}"
        ): row
        for row in serial_records
    }

    selected_serial_label = st.selectbox(
        "제품 Serial",
        options=list(serial_options.keys()),
        key="process_target_serial",
    )

    selected_serial = serial_options[selected_serial_label]


    info_col1, info_col2, info_col3, info_col4 = st.columns(4)

    with info_col1:
        st.metric(
            "작업지시",
            selected_serial["work_order_no"],
        )

    with info_col2:
        st.metric(
            "제품",
            selected_serial["item_code"],
        )

    with info_col3:
        st.metric(
            "다음 공정",
            selected_serial["process_name"],
        )

    with info_col4:
        st.metric(
            "공정 순서",
            int(selected_serial["sequence_no"]),
        )


    required_lots = get_required_material_lots(
        product_serial_id=int(
            selected_serial["product_serial_id"]
        ),
        routing_step_id=int(
            selected_serial["routing_step_id"]
        ),
    )

    st.divider()

    st.subheader("투입 자재 LOT 선택")


    if required_lots.empty:
        st.info("이 공정에는 투입할 BOM 자재가 없습니다.")

    material_groups = list(
        required_lots.groupby(
            [
                "material_item_id",
                "material_code",
                "material_name",
                "required_qty",
            ],
            dropna=False,
        )
    )

    has_unavailable_material = False
    selected_lot_ids: dict[int, int] = {}

    with st.form("process_result_form"):
        for material_key, material_lots in material_groups:
            (
                material_item_id,
                material_code,
                material_name,
                required_qty,
            ) = material_key

            available_lots = material_lots[
                material_lots["material_lot_id"].notna()
            ]

            st.markdown(
                f"**{material_code} - {material_name}** "
                f"(필요수량: {int(required_qty)}개)"
            )

            if available_lots.empty:
                st.error(
                    f"{material_name}의 사용 가능한 LOT가 없습니다."
                )
                has_unavailable_material = True
                continue

            lot_records = available_lots.to_dict(
                orient="records"
            )

            lot_options = {
                (
                    f"{row['lot_no']} | "
                    f"입고일 {row['received_date']} | "
                    f"잔여 {int(row['available_qty'])}개"
                ): int(row["material_lot_id"])
                for row in lot_records
            }

            selected_lot_label = st.selectbox(
                f"{material_name} LOT",
                options=list(lot_options.keys()),
                key=(
                    f"material_lot_"
                    f"{selected_serial['product_serial_id']}_"
                    f"{selected_serial['routing_step_id']}_"
                    f"{int(material_item_id)}"
                ),
            )

            selected_lot_ids[int(material_item_id)] = (
                lot_options[selected_lot_label]
            )

        remark = st.text_area(
            "비고",
            placeholder="작업 내용이나 특이사항을 입력하세요.",
        )

        result = st.radio(
            "공정 결과",
            options=["PASS", "FAIL"],
            horizontal=True,
        )

        if result == "FAIL":
            st.warning(
                "FAIL로 등록하면 해당 Serial은 종료되며 "
                "이후 공정을 진행할 수 없습니다."
            )

        submitted = st.form_submit_button(
            "공정 실적 등록",
            type="primary",
            disabled=has_unavailable_material,
        )

    if submitted:
        service_result = register_process_result(
            product_serial_id=int(
                selected_serial["product_serial_id"]
            ),
            routing_step_id=int(
                selected_serial["routing_step_id"]
            ),
            selected_lot_ids=selected_lot_ids,
            result=result,
            remark=remark,
        )

        if service_result.success:
            st.session_state["process_success_message"] = (
                service_result.message
            )
            st.rerun()
        else:
            st.error(service_result.message)

st.divider()
st.subheader("Serial별 등록 이력")

history_serials = get_history_serials()

if history_serials.empty:
    st.info("이력을 조회할 제품 Serial이 없습니다.")

else:
    history_status_labels = {
        "CREATED": "발급",
        "IN_PROGRESS": "생산 중",
        "PASS": "합격",
        "FAIL": "불합격",
    }

    history_serial_records = history_serials.to_dict(
        orient="records"
    )

    history_serial_options = {
        (
            f"{row['serial_no']} | "
            f"{row['item_code']} - {row['item_name']} | "
            f"{history_status_labels.get(
                row['serial_status'],
                row['serial_status'],
            )}"
        ): int(row["product_serial_id"])
        for row in history_serial_records
    }

    selected_history_label = st.selectbox(
        "이력 조회 Serial",
        options=list(history_serial_options.keys()),
        key="process_history_serial",
    )

    history_serial_id = history_serial_options[
        selected_history_label
    ]

    history_col1, history_col2 = st.columns(2)

    with history_col1:
        st.markdown("#### 공정 실적 이력")

        process_history = get_serial_process_history(
            history_serial_id
        )

        if process_history.empty:
            st.info("아직 등록된 공정 실적이 없습니다.")
        else:
            st.dataframe(
                process_history,
                use_container_width=True,
                hide_index=True,
            )

    with history_col2:
        st.markdown("#### 자재 LOT 소비 이력")

        material_consumptions = (
            get_serial_material_consumptions(
                history_serial_id
            )
        )

        if material_consumptions.empty:
            st.info("아직 등록된 자재 소비 이력이 없습니다.")
        else:
            st.dataframe(
                material_consumptions,
                use_container_width=True,
                hide_index=True,
            )
