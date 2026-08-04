from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from src.material_lot_service import (
    create_material_lot,
    get_active_materials,
    get_material_lots,
    get_status_changeable_material_lots,
    block_material_lot,
    get_available_stock_by_material,
    get_material_inventory_metrics,
)

from src.ui import (
    page_title,
    setup_page,
    show_dataframe,
)

def show_inventory_summary():
    """자재 재고 핵심 지표와 자재별 가용 재고 차트를 표시한다."""

    metrics = get_material_inventory_metrics()
    stock_df = get_available_stock_by_material()

    show_inventory_metrics(metrics)
    show_available_stock_chart(stock_df)

def show_inventory_metrics(metrics: dict):
    st.subheader("자재 재고 현황")

    column1, column2, column3, column4 = st.columns(4)

    column1.metric(
        label="전체 가용 재고",
        value=f"{metrics['available_stock_qty']:,}개",
    )

    column2.metric(
        label="사용 가능 LOT",
        value=f"{metrics['available_lot_count']:,}건",
    )

    column3.metric(
        label="차단 LOT",
        value=f"{metrics['blocked_lot_count']:,}건",
    )

    column4.metric(
        label="소진 LOT",
        value=f"{metrics['exhausted_lot_count']:,}건",
    )

def show_available_stock_chart(df: pd.DataFrame):
    st.subheader("자재별 가용 재고")

    if df.empty:
        st.info("표시할 자재 재고가 없습니다.")
        return

    chart = (
        alt.Chart(df)
        .mark_bar(
            color="#2563EB",
            cornerRadiusEnd=4,
        )
        .encode(
            x=alt.X(
                "available_qty:Q",
                title="가용 재고 수량",
                axis=alt.Axis(tickMinStep=1),
            ),
            y=alt.Y(
                "item_name:N",
                title=None,
                sort=alt.EncodingSortField(
                    field="available_qty",
                    order="descending",
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "item_code:N",
                    title="자재 코드",
                ),
                alt.Tooltip(
                    "item_name:N",
                    title="자재명",
                ),
                alt.Tooltip(
                    "available_qty:Q",
                    title="가용 재고",
                    format=",d",
                ),
            ],
        )
        .properties(height=280)
    )

    text = (
        alt.Chart(df)
        .mark_text(
            align="left",
            baseline="middle",
            dx=5,
            color="#334155",
        )
        .encode(
            x="available_qty:Q",
            y=alt.Y(
                "item_name:N",
                sort=alt.EncodingSortField(
                    field="available_qty",
                    order="descending",
                ),
            ),
            text=alt.Text(
                "available_qty:Q",
                format=",d",
            ),
        )
    )

    st.altair_chart(
        chart + text,
        width="stretch",
    )

    st.caption(
        "가용 재고는 사용 가능한 LOT의 입고수량에서 "
        "누적 투입수량을 제외한 값입니다."
    )


setup_page("자재 LOT 입고 관리")

page_title(
    title="자재 LOT 입고 관리",
)

materials = get_active_materials()

register_tab, search_tab, status_tab = st.tabs(
    [
        "신규 LOT 입고",
        "LOT 입고 내역 조회",
        "LOT 상태 관리",
    ]
)

with register_tab:
    if "material_lot_success_message" in st.session_state:
        st.success(
            st.session_state.pop(
                "material_lot_success_message"
            )
        )

    show_inventory_summary()
    
    st.divider()
    st.subheader("신규 자재 LOT 입고")

    if materials.empty:
        st.warning("입고 등록에 사용할 수 있는 활성 자재가 없습니다.")
    else:
        material_options = {
            f"{material.item_code} - {material.item_name}":
                material.item_id
            for material in materials.itertuples(index=False)
        }

        with st.form(
            "material_lot_register_form",
            clear_on_submit=True,
        ):
            selected_material = st.selectbox(
                "자재 선택",
                options=material_options.keys(),
            )

            lot_no = st.text_input(
                "LOT 번호",
                placeholder="예: LOT-MOTOR-20260804-001",
            )

            received_qty = st.number_input(
                "입고 수량",
                min_value=1,
                step=1,
            )

            received_date = st.date_input(
                "입고일",
            )

            submitted = st.form_submit_button(
                "자재 LOT 등록",
                type="primary",
            )

        if submitted:
            selected_material_id = material_options[
                selected_material
            ]

            result = create_material_lot(
                lot_no=lot_no,
                material_item_id=selected_material_id,
                received_qty=int(received_qty),
                received_date=received_date.isoformat(),
            )

            if result.success:
                st.session_state[
                    "material_lot_success_message"
                ] = result.message

                st.rerun()
            else:
                st.error(result.message)

with search_tab:
    st.subheader("자재 LOT 조회")

    material_filter_options = {
        "전체": None,
        **{
            f"{material.item_code} - {material.item_name}":
                material.item_id
            for material in materials.itertuples(index=False)
        },
    }

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
                options=list(material_filter_options.keys()),
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
                disabled=not use_received_date,
                key="lot_search_date_from",
            )

        with date_col2:
            received_date_to = st.date_input(
                "입고 종료일",
                value=date.today(),
                disabled=not use_received_date,
                key="lot_search_date_to",
            )

        st.form_submit_button(
            "조회",
            type="primary",
        )

    if use_received_date and received_date_from > received_date_to:
        st.error("입고 시작일은 종료일보다 늦을 수 없습니다.")

    else:
        lots = get_material_lots(
            material_item_id=material_filter_options[
                selected_search_material
            ],
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
