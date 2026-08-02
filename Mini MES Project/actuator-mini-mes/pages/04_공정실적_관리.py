from __future__ import annotations

import streamlit as st

from src.process_service import (
    get_process_ready_serials,
    get_required_material_lots,
    get_serial_material_consumptions,
    get_serial_process_history,
    register_process_result,
)
from src.ui import (
    page_title,
    setup_page,
    show_database_status,
)


setup_page("공정실적 관리")

page_title(
    title="공정실적 관리",
    description="제품 Serial별 다음 공정을 확인하고 공정 실적과 자재 소비 이력을 등록합니다.",
    tables="product_serial, routing_step, process_history, material_lot, material_consumption",
    task="Serial과 자재 LOT를 선택한 후 공정 실적을 등록합니다.",
)

show_database_status()

st.divider()
st.subheader("공정 투입 대상 선택")

if "process_success_message" in st.session_state:
    st.success(
        st.session_state.pop("process_success_message")
    )

ready_serials = get_process_ready_serials()

if ready_serials.empty:
    st.info("현재 공정 실적을 등록할 수 있는 Serial이 없습니다.")
    st.stop()


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

    submitted = st.form_submit_button(
        "공정 실적 등록",
        type="primary",
        disabled=has_unavailable_material,
    )


if submitted:
    result = register_process_result(
        product_serial_id=int(
            selected_serial["product_serial_id"]
        ),
        routing_step_id=int(
            selected_serial["routing_step_id"]
        ),
        selected_lot_ids=selected_lot_ids,
        result="PASS",
        remark=remark,
    )

    if result.success:
        st.session_state["process_success_message"] = (
            result.message
        )
        st.rerun()
    else:
        st.error(result.message)

st.divider()
st.subheader("선택한 Serial의 등록 이력")

history_col1, history_col2 = st.columns(2)

with history_col1:
    st.markdown("#### 공정 실적 이력")

    process_history = get_serial_process_history(
        int(selected_serial["product_serial_id"])
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

    material_consumptions = get_serial_material_consumptions(
        int(selected_serial["product_serial_id"])
    )

    if material_consumptions.empty:
        st.info("아직 등록된 자재 소비 이력이 없습니다.")
    else:
        st.dataframe(
            material_consumptions,
            use_container_width=True,
            hide_index=True,
        )
