from __future__ import annotations

from datetime import date

import streamlit as st

from src.material_lot_service import (
    create_material_lot,
    get_active_materials,
    get_material_lots,
    get_status_changeable_material_lots,
    block_material_lot,
)

from src.ui import (
    page_title,
    setup_page,
    show_database_status,
    show_dataframe,
)


setup_page("자재 LOT 입고 관리")

page_title(
    title="자재 LOT 입고 관리",
    description="입고된 자재를 LOT 단위로 등록하고 조회합니다.",
    tables="item, material_lot",
    task="자재와 입고 정보를 입력하여 신규 자재 LOT을 등록합니다.",
)

show_database_status()

register_tab, search_tab, status_tab = st.tabs(
    [
        "신규 LOT 입고",
        "LOT 입고 내역 조회",
        "LOT 상태 관리",
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
    st.subheader("자재 LOT 입고 내역 조회")

    materials = get_active_materials()

    material_options = {
        "전체 자재": None,
    }

    material_options.update(
        {
            f"{row['item_code']} - {row['item_name']}": row["item_id"]
            for row in materials.to_dict(orient="records")
        }
    )

    status_options = {
        "전체 상태": None,
        "사용 가능": "AVAILABLE",
        "소진": "EXHAUSTED",
        "사용 중지": "BLOCKED",
    }

    with st.form("material_lot_search_form"):
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            selected_search_material = st.selectbox(
                "자재",
                options=list(material_options.keys()),
                key="lot_search_material",
            )

            keyword = st.text_input(
                "LOT 번호 검색",
                placeholder="LOT 번호의 일부를 입력하세요.",
                key="lot_search_keyword",
            )

        with filter_col2:
            selected_status = st.selectbox(
                "LOT 상태",
                options=list(status_options.keys()),
                key="lot_search_status",
            )

            use_received_date = st.checkbox(
                "입고일 범위 사용",
                key="lot_search_use_date",
            )

        date_col1, date_col2 = st.columns(2)

        with date_col1:
            received_date_from = st.date_input(
                "입고 시작일",
                value=date.today(),
                key="lot_search_date_from",
            )

        with date_col2:
            received_date_to = st.date_input(
                "입고 종료일",
                value=date.today(),
                key="lot_search_date_to",
            )

        search_submitted = st.form_submit_button(
            "조회",
            type="primary",
        )

    if use_received_date and received_date_from > received_date_to:
        st.error("입고 시작일은 종료일보다 늦을 수 없습니다.")
    else:
        lots = get_material_lots(
            material_item_id=material_options[selected_search_material],
            status=status_options[selected_status],
            keyword=keyword,
            received_date_from=(
                received_date_from.isoformat()
                if use_received_date
                else None
            ),
            received_date_to=(
                received_date_to.isoformat()
                if use_received_date
                else None
            ),
        )

        st.caption(f"조회 결과: {len(lots):,}건")

        show_dataframe(
            lots,
            empty_message="조건에 해당하는 자재 LOT이 없습니다.",
        )

with status_tab:
    st.subheader("자재 LOT 사용 중지")

    if "lot_status_success_message" in st.session_state:
        st.success(
            st.session_state.pop("lot_status_success_message")
        )

    st.info(
        """
        품질 이상이나 공급업체 확인 등의 이유로
        생산에 투입하면 안 되는 LOT을 사용 중지합니다.

        사용 중지된 LOT은 이 화면에서 바로 해제할 수 없습니다.
        """
    )

    changeable_lots = get_status_changeable_material_lots()

    if changeable_lots.empty:
        st.warning("사용 중지할 수 있는 자재 LOT이 없습니다.")

    else:
        lot_options = {}

        for lot in changeable_lots.itertuples(index=False):
            option_label = (
                f"{lot.lot_no} | "
                f"{lot.item_code} - {lot.item_name} | "
                f"잔여 {lot.remaining_qty:,}개"
            )

            lot_options[option_label] = {
                "material_lot_id": lot.material_lot_id,
                "lot_no": lot.lot_no,
                "status": lot.status,
                "remaining_qty": lot.remaining_qty,
            }

        selected_lot_label = st.selectbox(
            "사용 중지할 LOT",
            options=list(lot_options.keys()),
            key="status_change_lot",
        )

        selected_lot = lot_options[selected_lot_label]

        detail_col1, detail_col2, detail_col3 = st.columns(3)

        with detail_col1:
            st.metric(
                "LOT 번호",
                selected_lot["lot_no"],
            )

        with detail_col2:
            st.metric(
                "현재 상태",
                "사용 가능",
            )

        with detail_col3:
            st.metric(
                "잔여 수량",
                f"{selected_lot['remaining_qty']:,}개",
            )

        st.divider()

        st.warning(
            "사용 중지 후에는 생산 공정의 자재 선택 목록에서 제외됩니다."
        )

        with st.form("material_lot_block_form"):
            blocked_reason = st.text_area(
                "사용 중지 사유",
                placeholder=(
                    "예: 입고 검사 중 외관 손상이 발견되어 "
                    "공급업체 품질 확인이 필요함"
                ),
                max_chars=500,
                help="LOT을 사용 중지하는 구체적인 이유를 입력합니다.",
            )

            block_submitted = st.form_submit_button(
                "선택한 LOT 사용 중지",
                type="primary",
            )

        if block_submitted:
            result = block_material_lot(
                material_lot_id=selected_lot["material_lot_id"],
                blocked_reason=blocked_reason,
            )

            if result.success:
                st.session_state[
                    "lot_status_success_message"
                ] = result.message
                st.rerun()
            else:
                st.error(result.message)
