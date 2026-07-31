from __future__ import annotations

from datetime import date

import streamlit as st

from src.material_lot_service import (
    create_material_lot,
    get_active_materials,
    get_material_lots,
)
from src.ui import page_title, setup_page, show_database_status


setup_page("자재 LOT 입고 관리")

page_title(
    title="자재 LOT 입고 관리",
    description="입고된 자재를 LOT 단위로 등록하고 조회합니다.",
    tables="item, material_lot",
    task="자재와 입고 정보를 입력하여 신규 자재 LOT을 등록합니다.",
)

show_database_status()

register_tab, search_tab = st.tabs(
    [
        "신규 LOT 입고",
        "LOT 입고 내역 조회",
    ]
)

with register_tab:
    st.subheader("신규 자재 LOT 입고")

    materials = get_active_materials()

    material_options = {
        f"{material['item_code']} - {material['item_name']}": material["item_id"]
        for material in materials.to_dict(orient="records")
    }

    if materials.empty:
        st.warning("입고 등록에 사용할 수 있는 활성 자재가 없습니다.")
    else:
        material_options = {
            f"{material.item_code} - {material.item_name}": material.item_id
            for material in materials.itertuples(index=False)
        }

        with st.form("material_lot_register_form"):
            selected_material = st.selectbox(
                "자재",
                options=material_options.keys(),
            )

            lot_no = st.text_input(
                "LOT 번호",
                placeholder="예: LOT-MOTOR-20260731-D",
                help="공급처 또는 입고 묶음을 구분할 수 있는 고유 번호입니다.",
            )

            received_qty = st.number_input(
                "입고 수량",
                min_value=1,
                value=1,
                step=1,
            )

            received_date = st.date_input(
                "입고일",
                value=date.today(),
                max_value=date.today(),
            )

            submitted = st.form_submit_button(
                "LOT 입고 등록",
                type="primary",
            )

        if submitted:
            selected_material_id = material_options[selected_material]

            result = create_material_lot(
                lot_no=lot_no,
                material_item_id=selected_material_id,
                received_qty=int(received_qty),
                received_date=received_date.isoformat(),
            )

            if result.success:
                st.success(result.message)
            else:
                st.error(result.message)

with search_tab:
    st.info("자재 LOT 입고 내역 조회 화면은 다음 단계에서 구현합니다.")
