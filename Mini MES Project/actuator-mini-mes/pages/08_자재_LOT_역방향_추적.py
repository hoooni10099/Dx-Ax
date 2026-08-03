from __future__ import annotations

import streamlit as st

from src.traceability_service import (
    get_lot_serial_trace,
    get_material_lot_options,
    get_material_lot_summary,
)
from src.ui import page_title, setup_page, show_database_status


setup_page("LOT 추적")

page_title(
    title="LOT 역방향 추적",
    description=(
        "자재 LOT를 기준으로 자재 기본정보와 수량 현황을 확인하고, "
        "해당 LOT가 투입된 완제품 Serial을 조회합니다."
    ),
    tables=(
        "material_lot, material_consumption, item, "
        "product_serial, work_order, routing_step, process"
    ),
    task="자재 LOT를 선택하고 해당 자재가 사용된 완제품을 확인합니다.",
)

show_database_status()

st.divider()

lot_options_dataframe = get_material_lot_options()

if lot_options_dataframe.empty:
    st.info("추적할 자재 LOT가 없습니다.")

else:
    lot_options_dataframe["display_label"] = (
        lot_options_dataframe["lot_no"]
        + " | "
        + lot_options_dataframe["material_code"]
        + " | "
        + lot_options_dataframe["material_name"]
    )

    lot_option_map = dict(
        zip(
            lot_options_dataframe["display_label"],
            lot_options_dataframe["material_lot_id"],
        )
    )

    selected_lot_label = st.selectbox(
        "추적할 자재 LOT",
        options=list(lot_option_map.keys()),
    )

    selected_material_lot_id = lot_option_map[
        selected_lot_label
    ]

    lot_summary = get_material_lot_summary(
        selected_material_lot_id
    )

    if lot_summary.empty:
        st.warning("선택한 자재 LOT의 기본정보를 찾을 수 없습니다.")

    else:
        summary = lot_summary.iloc[0]

        st.divider()
        st.subheader("자재 LOT 기본정보")

        column1, column2, column3, column4 = st.columns(4)

        with column1:
            st.metric(
                "LOT 번호",
                summary["lot_no"],
            )

        with column2:
            st.metric(
                "자재 코드",
                summary["material_code"],
            )

        with column3:
            st.metric(
                "LOT 상태",
                summary["lot_status"],
            )

        with column4:
            st.metric(
                "잔여 수량",
                int(summary["remaining_qty"]),
            )

        quantity_column1, quantity_column2, quantity_column3 = (
            st.columns(3)
        )

        with quantity_column1:
            st.metric(
                "입고 수량",
                int(summary["received_qty"]),
            )

        with quantity_column2:
            st.metric(
                "누적 투입 수량",
                int(summary["consumed_qty"]),
            )

        with quantity_column3:
            usage_rate = (
                summary["consumed_qty"]
                / summary["received_qty"]
                * 100
            )

            st.metric(
                "소진율",
                f"{usage_rate:.1f}%",
            )

        summary_display = lot_summary.rename(
            columns={
                "lot_no": "LOT 번호",
                "material_code": "자재 코드",
                "material_name": "자재명",
                "received_qty": "입고 수량",
                "consumed_qty": "누적 투입 수량",
                "remaining_qty": "잔여 수량",
                "received_date": "입고일",
                "lot_status": "LOT 상태",
                "created_at": "등록 시각",
            }
        )

        st.dataframe(
            summary_display[
                [
                    "LOT 번호",
                    "자재 코드",
                    "자재명",
                    "입고 수량",
                    "누적 투입 수량",
                    "잔여 수량",
                    "입고일",
                    "LOT 상태",
                    "등록 시각",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("LOT 투입 완제품 Serial")

        lot_serial_trace = get_lot_serial_trace(
            selected_material_lot_id
        )

        if lot_serial_trace.empty:
            st.info(
                "이 자재 LOT가 투입된 완제품 Serial이 없습니다."
            )

        else:
            serial_count = (
                lot_serial_trace["product_serial_id"].nunique()
            )

            total_consumed_qty = (
                lot_serial_trace["consumed_qty"].sum()
            )

            serial_column, quantity_column = st.columns(2)

            with serial_column:
                st.metric(
                    "투입된 완제품 수",
                    serial_count,
                )

            with quantity_column:
                st.metric(
                    "총 투입 수량",
                    int(total_consumed_qty),
                )

            trace_display = lot_serial_trace.rename(
                columns={
                    "serial_no": "Serial 번호",
                    "serial_status": "Serial 상태",
                    "work_order_no": "작업지시 번호",
                    "work_order_status": "작업지시 상태",
                    "product_code": "제품 코드",
                    "product_name": "제품명",
                    "sequence_no": "공정 순서",
                    "process_code": "공정 코드",
                    "process_name": "투입 공정",
                    "consumed_qty": "투입 수량",
                    "consumed_at": "투입 시각",
                }
            )

            st.dataframe(
                trace_display[
                    [
                        "Serial 번호",
                        "제품 코드",
                        "제품명",
                        "Serial 상태",
                        "작업지시 번호",
                        "작업지시 상태",
                        "공정 순서",
                        "공정 코드",
                        "투입 공정",
                        "투입 수량",
                        "투입 시각",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )
