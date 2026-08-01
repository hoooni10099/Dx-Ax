from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from src.work_order_service import (
    create_work_order,
    get_active_products,
    get_product_serials,
    get_serial_issuable_work_orders,
    get_work_orders,
    issue_product_serials,
)
from src.ui import (
    page_title,
    setup_page,
    show_database_status,
    show_dataframe,
)

setup_page("작업지시 관리")

page_title(
    title="작업지시 관리",
    description="생산할 제품과 계획수량, 납기일을 지정하여 작업지시를 등록합니다.",
    tables="work_order, item",
    task="신규 작업지시를 생성하고 등록 결과를 확인합니다.",
)

show_database_status()

register_tab, search_tab, serial_tab = st.tabs(
    [
        "작업지시 등록",
        "작업지시 조회",
        "Serial 발급",
    ]
)


with register_tab:
    st.subheader("신규 작업지시 등록")

    products = get_active_products()

    if products.empty:
        st.warning("작업지시를 생성할 수 있는 활성 완제품이 없습니다.")

    else:
        product_options = {
            f"{row['item_code']} - {row['item_name']}": row["item_id"]
            for row in products.to_dict(orient="records")
        }

        with st.form(
            "work_order_register_form",
            clear_on_submit=False,
        ):
            work_order_no = st.text_input(
                "작업지시 번호",
                placeholder="예: WO-20260801-002",
            )

            selected_product = st.selectbox(
                "생산 제품",
                options=list(product_options.keys()),
            )

            input_col1, input_col2 = st.columns(2)

            with input_col1:
                planned_qty = st.number_input(
                    "계획수량",
                    min_value=1,
                    value=10,
                    step=1,
                )

            with input_col2:
                due_date = st.date_input(
                    "납기일",
                    value=date.today() + timedelta(days=7),
                    min_value=date.today(),
                )

            submitted = st.form_submit_button(
                "작업지시 등록",
                type="primary",
            )

        if submitted:
            result = create_work_order(
                work_order_no=work_order_no,
                product_item_id=product_options[selected_product],
                planned_qty=int(planned_qty),
                due_date=due_date.isoformat(),
            )

            if result.success:
                st.success(result.message)
            else:
                st.error(result.message)


with search_tab:
    st.subheader("작업지시 조회")

    products = get_active_products()

    search_product_options = {
        "전체 제품": None,
    }

    search_product_options.update(
        {
            f"{row['item_code']} - {row['item_name']}": row["item_id"]
            for row in products.to_dict(orient="records")
        }
    )

    status_options = {
        "전체 상태": None,
        "계획": "PLANNED",
        "생산 중": "IN_PROGRESS",
        "완료": "COMPLETED",
        "취소": "CANCELLED",
    }

    with st.form("work_order_search_form"):
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            selected_search_product = st.selectbox(
                "생산 제품",
                options=list(search_product_options.keys()),
                key="work_order_search_product",
            )

        with filter_col2:
            selected_search_status = st.selectbox(
                "작업지시 상태",
                options=list(status_options.keys()),
                key="work_order_search_status",
            )

        keyword = st.text_input(
            "검색어",
            placeholder="작업지시 번호, 제품코드 또는 제품명을 입력하세요.",
            key="work_order_search_keyword",
        )

        search_submitted = st.form_submit_button(
            "조회",
            type="primary",
        )

    work_orders = get_work_orders(
        product_item_id=search_product_options[selected_search_product],
        status=status_options[selected_search_status],
        keyword=keyword,
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric(
            "작업지시 건수",
            f"{len(work_orders):,}건",
        )

    with metric_col2:
        planned_qty_total = (
            int(work_orders["계획수량"].sum())
            if not work_orders.empty
            else 0
        )

        st.metric(
            "총 계획수량",
            f"{planned_qty_total:,}개",
        )

    with metric_col3:
        issued_qty_total = (
            int(work_orders["Serial발급수량"].sum())
            if not work_orders.empty
            else 0
        )

        st.metric(
            "Serial 발급수량",
            f"{issued_qty_total:,}개",
        )

    show_dataframe(
        work_orders,
        empty_message="조건에 해당하는 작업지시가 없습니다.",
    )

with serial_tab:
    st.subheader("제품 Serial Number 발급")

    if "serial_success_message" in st.session_state:
        st.success(st.session_state.pop("serial_success_message"))

    issuable_work_orders = get_serial_issuable_work_orders()

    if issuable_work_orders.empty:
        st.info("Serial을 추가로 발급할 수 있는 작업지시가 없습니다.")

    else:
        work_order_records = issuable_work_orders.to_dict(
            orient="records"
        )

        work_order_options = {
            (
                f"{row['work_order_no']} | "
                f"{row['item_code']} - {row['item_name']} | "
                f"잔여 {row['remaining_qty']}개"
            ): row
            for row in work_order_records
        }

        selected_work_order_label = st.selectbox(
            "작업지시 선택",
            options=list(work_order_options.keys()),
            key="serial_issue_work_order",
        )

        selected_work_order = work_order_options[
            selected_work_order_label
        ]

        metric_col1, metric_col2, metric_col3 = st.columns(3)

        with metric_col1:
            st.metric(
                "계획수량",
                f"{int(selected_work_order['planned_qty']):,}개",
            )

        with metric_col2:
            st.metric(
                "발급수량",
                f"{int(selected_work_order['issued_qty']):,}개",
            )

        with metric_col3:
            st.metric(
                "발급 가능수량",
                f"{int(selected_work_order['remaining_qty']):,}개",
            )

        with st.form("serial_issue_form"):
            issue_qty = st.number_input(
                "이번 발급수량",
                min_value=1,
                max_value=int(
                    selected_work_order["remaining_qty"]
                ),
                value=1,
                step=1,
            )

            issue_submitted = st.form_submit_button(
                "Serial 발급",
                type="primary",
            )

        if issue_submitted:
            result = issue_product_serials(
                work_order_id=int(
                    selected_work_order["work_order_id"]
                ),
                issue_qty=int(issue_qty),
            )

            if result.success:
                st.session_state["serial_success_message"] = result.message
                st.rerun()
            else:
                st.error(result.message)

        st.divider()
    st.subheader("발급된 제품 Serial 조회")

    serial_keyword = st.text_input(
        "Serial 검색",
        placeholder="Serial Number, 작업지시번호, 제품코드 또는 제품명을 입력하세요.",
        key="serial_search_keyword",
    )

    product_serials = get_product_serials()

    if serial_keyword.strip() and not product_serials.empty:
        normalized_keyword = serial_keyword.strip().lower()

        search_columns = [
            "Serial Number",
            "작업지시번호",
            "제품코드",
            "제품명",
        ]

        search_mask = product_serials[search_columns].apply(
            lambda column: (
                column.astype(str)
                .str.lower()
                .str.contains(
                    normalized_keyword,
                    regex=False,
                    na=False,
                )
            )
        ).any(axis=1)

        product_serials = product_serials[search_mask]

    st.metric(
        "조회된 Serial",
        f"{len(product_serials):,}건",
    )

    show_dataframe(
        product_serials,
        empty_message="조건에 해당하는 제품 Serial이 없습니다.",
    )
