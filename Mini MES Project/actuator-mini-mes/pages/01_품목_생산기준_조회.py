from __future__ import annotations

import streamlit as st

from src.master_data_service import (
    get_bom_by_product,
    get_items,
    get_products,
    get_routing_by_product,
)
from src.ui import (
    page_title,
    setup_page,
    show_database_status,
    show_dataframe,
)

PAGE_TITLE = "품목, 생산기준 조회"

ITEM_TYPE_OPTIONS = {
    "전체" : None,
    "제품" : "PRODUCT",
    "자재" : "MATERIAL",
}

ACTIVE_STATUS_OPTIONS = {
    "전체" : None,
    "사용" : 1,
    "미사용" : 0,
}

setup_page(PAGE_TITLE)

page_title(
    title = PAGE_TITLE,
    description = "품목, BOM, 제품별 공정순서로 구성된 생산 기준정보를 조회합니다.",
    tables = "item, bom, routing_step, process",
    task = "조회 조건을 선택하여 등록된 생산 기준정보를 확인합니다.",
)

show_database_status()

item_tab, bom_tab, routing_tab = st.tabs(
    [
        "품목 조회",
        "제품별 BOM",
        "제품별 공정순서",
    ]
)


with item_tab:
    st.subheader("품목 조회")

    item_type_column, active_status_column, keyword_column = st.columns(
        [1, 1, 2]
    )

    with item_type_column:
        selected_item_type = st.selectbox(
            "품목 유형",
            options=ITEM_TYPE_OPTIONS.keys(),
        )

    with active_status_column:
        selected_active_status = st.selectbox(
            "활성 상태",
            options=ACTIVE_STATUS_OPTIONS.keys(),
        )

    with keyword_column:
        keyword = st.text_input(
            "검색어",
            placeholder="품목코드 또는 품목명을 입력하세요.",
        )

    items = get_items(
        item_type=ITEM_TYPE_OPTIONS[selected_item_type],
        is_active=ACTIVE_STATUS_OPTIONS[selected_active_status],
        keyword=keyword,
    )

    st.caption(f"조회 결과: {len(items)}건")

    show_dataframe(
        items,
        empty_message="조회 조건에 해당하는 품목이 없습니다.",
    )


with bom_tab:
    st.subheader("제품별 BOM")

    products = get_products()

    if products.empty:
        st.warning("조회할 수 있는 활성 제품이 없습니다.")
    else:
        product_options = {
            f"{product.item_code} - {product.item_name}": product.item_id
            for product in products.itertuples(index=False)
        }

        selected_product = st.selectbox(
            "제품 선택",
            options=product_options.keys(),
        )

        selected_product_id = product_options[selected_product]

        bom = get_bom_by_product(selected_product_id)

        st.caption(f"조회 결과: {len(bom)}건")

        show_dataframe(
            bom,
            empty_message="선택한 제품에 등록된 BOM이 없습니다.",
        )

with routing_tab:
    st.subheader("제품별 공정순서")

    products = get_products()

    if products.empty:
        st.warning("조회할 수 있는 활성 제품이 없습니다.")
    else:
        routing_product_options = {
            f"{product.item_code} - {product.item_name}": product.item_id
            for product in products.itertuples(index=False)
        }

        selected_routing_product = st.selectbox(
            "제품 선택",
            options=routing_product_options.keys(),
            key="routing_product",
        )

        selected_routing_product_id = routing_product_options[
            selected_routing_product
        ]

        routing = get_routing_by_product(
            selected_routing_product_id
        )

        st.caption(f"조회 결과: {len(routing)}건")

        show_dataframe(
            routing,
            empty_message="선택한 제품에 등록된 공정순서가 없습니다.",
        )
