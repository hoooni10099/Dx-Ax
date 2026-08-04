from __future__ import annotations

import streamlit as st
import altair as alt
import pandas as pd

from src.production_status_service import (
    get_production_status,
    get_serial_process_status,
    get_serial_status,
)
from src.ui import page_title, setup_page

def show_work_order_production_chart(
    status_df: pd.DataFrame,
):
    """작업지시별 계획 수량과 Serial 상태 수량을 비교한다."""

    st.subheader("작업지시별 계획 대비 생산 현황")

    if status_df.empty:
        st.info("표시할 작업지시 생산 현황이 없습니다.")
        return

    required_columns = {
        "work_order_no",
        "planned_qty",
        "created_qty",
        "in_progress_qty",
        "pass_qty",
        "fail_qty",
    }

    missing_columns = required_columns - set(status_df.columns)

    if missing_columns:
        st.error(
            "생산 현황 차트에 필요한 컬럼이 없습니다: "
            + ", ".join(sorted(missing_columns))
        )
        return

    chart_df = status_df[
        [
            "work_order_no",
            "planned_qty",
            "created_qty",
            "in_progress_qty",
            "pass_qty",
            "fail_qty",
        ]
    ].copy()

    chart_df = chart_df.rename(
        columns={
            "planned_qty": "계획",
            "created_qty": "시작 전",
            "in_progress_qty": "진행 중",
            "pass_qty": "합격 종료",
            "fail_qty": "불합격 종료",
        }
    )

    long_df = chart_df.melt(
        id_vars=["work_order_no"],
        value_vars=[
            "계획",
            "시작 전",
            "진행 중",
            "합격 종료",
            "불합격 종료",
        ],
        var_name="production_status",
        value_name="quantity",
    )

    long_df["quantity"] = (
        pd.to_numeric(
            long_df["quantity"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )

    long_df["bar_group"] = long_df[
        "production_status"
    ].map(
        {
            "계획": "계획 수량",
            "시작 전": "Serial 현황",
            "진행 중": "Serial 현황",
            "합격 종료": "Serial 현황",
            "불합격 종료": "Serial 현황",
        }
    )

    work_order_order = (
        chart_df["work_order_no"]
        .drop_duplicates()
        .tolist()
    )

    chart = (
        alt.Chart(long_df)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X(
                "quantity:Q",
                title="수량",
                axis=alt.Axis(tickMinStep=1),
            ),
            y=alt.Y(
                "work_order_no:N",
                title="작업지시",
                sort=work_order_order,
            ),
            yOffset=alt.YOffset(
                "bar_group:N",
                title=None,
                sort=["계획 수량", "Serial 현황"],
            ),
            color=alt.Color(
                "production_status:N",
                title="구분",
                scale=alt.Scale(
                    domain=[
                        "계획",
                        "시작 전",
                        "진행 중",
                        "합격 종료",
                        "불합격 종료",
                    ],
                    range=[
                        "#64748B",
                        "#CBD5E1",
                        "#2563EB",
                        "#16A34A",
                        "#DC2626",
                    ],
                ),
            ),
            order=alt.Order(
                "production_status:N",
                sort="ascending",
            ),
            tooltip=[
                alt.Tooltip(
                    "work_order_no:N",
                    title="작업지시",
                ),
                alt.Tooltip(
                    "bar_group:N",
                    title="막대 구분",
                ),
                alt.Tooltip(
                    "production_status:N",
                    title="상태",
                ),
                alt.Tooltip(
                    "quantity:Q",
                    title="수량",
                    format=",d",
                ),
            ],
        )
        .properties(
            height=max(300, len(chart_df) * 55),
        )
    )

    st.altair_chart(
        chart,
        width="stretch",
    )

def show_serial_status_chart(
    serial_df: pd.DataFrame,
    work_order_no: str,
):
    """선택한 작업지시의 Serial 상태별 수량을 표시한다."""

    st.subheader("Serial 상태 구성")

    if serial_df.empty:
        st.info("표시할 Serial 상태 정보가 없습니다.")
        return

    if "status" not in serial_df.columns:
        st.error("Serial 상태 차트에 필요한 status 컬럼이 없습니다.")
        return

    status_order = [
        "CREATED",
        "IN_PROGRESS",
        "PASS",
        "FAIL",
    ]

    status_names = {
        "CREATED": "시작 전",
        "IN_PROGRESS": "진행 중",
        "PASS": "합격 종료",
        "FAIL": "불합격 종료",
    }

    status_colors = {
        "시작 전": "#CBD5E1",
        "진행 중": "#2563EB",
        "합격 종료": "#16A34A",
        "불합격 종료": "#DC2626",
    }

    # 실제 존재하는 상태별 Serial 수량 계산
    status_counts = (
        serial_df["status"]
        .value_counts()
        .reindex(
            status_order,
            fill_value=0,
        )
        .rename_axis("status")
        .reset_index(name="quantity")
    )

    status_counts["status_name"] = (
        status_counts["status"].map(status_names)
    )

    status_name_order = [
        status_names[status]
        for status in status_order
    ]

    chart = (
        alt.Chart(status_counts)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(
                "quantity:Q",
                title="Serial 수량",
                axis=alt.Axis(tickMinStep=1),
            ),
            y=alt.Y(
                "status_name:N",
                title=None,
                sort=status_name_order,
            ),
            color=alt.Color(
                "status_name:N",
                title="Serial 상태",
                scale=alt.Scale(
                    domain=status_name_order,
                    range=[
                        status_colors[status_name]
                        for status_name in status_name_order
                    ],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip(
                    "status_name:N",
                    title="상태",
                ),
                alt.Tooltip(
                    "quantity:Q",
                    title="수량",
                    format=",d",
                ),
            ],
        )
        .properties(
            title=f"{work_order_no} Serial 상태별 수량",
            height=220,
        )
    )

    text = (
        alt.Chart(status_counts)
        .mark_text(
            align="left",
            baseline="middle",
            dx=5,
            fontSize=13,
        )
        .encode(
            x=alt.X("quantity:Q"),
            y=alt.Y(
                "status_name:N",
                sort=status_name_order,
            ),
            text=alt.Text(
                "quantity:Q",
                format=",d",
            ),
        )
    )

    st.altair_chart(
        chart + text,
        width="stretch",
    )

def show_process_waiting_chart(
    serial_df: pd.DataFrame,
    work_order_no: str,
):
    """선택한 작업지시의 다음 공정별 대기 Serial 수량을 표시한다."""

    st.subheader("공정별 대기 Serial 수량")

    if serial_df.empty:
        st.info("표시할 공정 대기 정보가 없습니다.")
        return

    required_columns = {
        "status",
        "next_process_name",
    }

    missing_columns = required_columns - set(serial_df.columns)

    if missing_columns:
        st.error(
            "공정 대기 차트에 필요한 컬럼이 없습니다: "
            + ", ".join(sorted(missing_columns))
        )
        return

    # 생산이 종료되지 않았고 다음 공정이 존재하는 Serial만 집계
    waiting_df = serial_df[
        serial_df["status"].isin(
            ["CREATED", "IN_PROGRESS"]
        )
        & serial_df["next_process_name"].notna()
    ].copy()

    if waiting_df.empty:
        st.info(
            "현재 다음 공정을 기다리는 Serial이 없습니다."
        )
        return

    waiting_counts = (
        waiting_df.groupby(
            "next_process_name",
            as_index=False,
        )
        .size()
        .rename(
            columns={
                "size": "quantity",
            }
        )
    )

    # 대기 수량이 많은 공정부터 표시
    waiting_counts = waiting_counts.sort_values(
        by="quantity",
        ascending=False,
    )

    process_order = waiting_counts[
        "next_process_name"
    ].tolist()

    chart = (
        alt.Chart(waiting_counts)
        .mark_bar(
            cornerRadiusEnd=4,
            color="#F59E0B",
        )
        .encode(
            x=alt.X(
                "quantity:Q",
                title="대기 Serial 수량",
                axis=alt.Axis(tickMinStep=1),
            ),
            y=alt.Y(
                "next_process_name:N",
                title="다음 공정",
                sort=process_order,
            ),
            tooltip=[
                alt.Tooltip(
                    "next_process_name:N",
                    title="대기 공정",
                ),
                alt.Tooltip(
                    "quantity:Q",
                    title="Serial 수량",
                    format=",d",
                ),
            ],
        )
        .properties(
            title=f"{work_order_no} 공정별 대기 현황",
            height=max(
                220,
                len(waiting_counts) * 45,
            ),
        )
    )

    text = (
        alt.Chart(waiting_counts)
        .mark_text(
            align="left",
            baseline="middle",
            dx=5,
            fontSize=13,
        )
        .encode(
            x=alt.X("quantity:Q"),
            y=alt.Y(
                "next_process_name:N",
                sort=process_order,
            ),
            text=alt.Text(
                "quantity:Q",
                format=",d",
            ),
        )
    )

    st.altair_chart(
        chart + text,
        width="stretch",
    )



setup_page("생산 진행 현황")

page_title(
    title="생산 진행 현황",
)

st.divider()

production_status = get_production_status()

if production_status.empty:
    st.info("조회할 작업지시가 없습니다.")

else:
    st.subheader("조회 조건")

    filter_column1, filter_column2 = st.columns(2)

    status_options = [
        "전체",
        *sorted(
            production_status["status"]
            .dropna()
            .unique()
            .tolist()
        ),
    ]

    item_code_options = [
        "전체",
        *sorted(
            production_status["item_code"]
            .dropna()
            .unique()
            .tolist()
        ),
    ]

    with filter_column1:
        selected_status = st.selectbox(
            "작업지시 상태",
            options=status_options,
        )

    with filter_column2:
        selected_item_code = st.selectbox(
            "제품 코드",
            options=item_code_options,
        )

    filtered_status = production_status.copy()

    if selected_status != "전체":
        filtered_status = filtered_status[
            filtered_status["status"] == selected_status
        ]

    if selected_item_code != "전체":
        filtered_status = filtered_status[
            filtered_status["item_code"] == selected_item_code
        ]

    if filtered_status.empty:
        st.warning("선택한 조건에 해당하는 작업지시가 없습니다.")

    else:
        total_planned_qty = int(
            filtered_status["planned_qty"].sum()
        )
        total_finished_qty = int(
            filtered_status["finished_qty"].sum()
        )
        total_pass_qty = int(
            filtered_status["pass_qty"].sum()
        )
        total_fail_qty = int(
            filtered_status["fail_qty"].sum()
        )

        column1, column2, column3, column4 = st.columns(4)

        with column1:
            st.metric("전체 계획 수량", total_planned_qty)

        with column2:
            st.metric("전체 종료 수량", total_finished_qty)

        with column3:
            st.metric("합격 수량", total_pass_qty)

        with column4:
            st.metric("불합격 수량", total_fail_qty)

        st.divider()

        # 작업지시별 계획 대비 생산 현황 차트
        show_work_order_production_chart(filtered_status)

        st.divider()

        st.subheader("작업지시별 진행 현황")

        display_dataframe = filtered_status.rename(
            columns={
                "work_order_no": "작업지시 번호",
                "item_code": "제품 코드",
                "item_name": "제품명",
                "planned_qty": "계획",
                "issued_qty": "발급",
                "created_qty": "시작 전",
                "in_progress_qty": "진행 중",
                "pass_qty": "합격",
                "fail_qty": "불합격",
                "finished_qty": "종료",
                "progress_rate": "진행률(%)",
                "status": "작업지시 상태",
                "due_date": "납기일",
                "started_at": "시작 시각",
                "completed_at": "완료 시각",
            }
        )

        st.dataframe(
            display_dataframe[
                [
                    "작업지시 번호",
                    "제품 코드",
                    "제품명",
                    "계획",
                    "발급",
                    "시작 전",
                    "진행 중",
                    "합격",
                    "불합격",
                    "종료",
                    "진행률(%)",
                    "작업지시 상태",
                    "납기일",
                    "시작 시각",
                    "완료 시각",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("Serial별 진행 현황")

        work_order_options = dict(
            zip(
                filtered_status["work_order_no"],
                filtered_status["work_order_id"],
            )
        )

        selected_work_order_no = st.selectbox(
            "상세 조회할 작업지시",
            options=list(work_order_options.keys()),
        )

        selected_work_order_id = work_order_options[
            selected_work_order_no
        ]

        serial_status = get_serial_status(
            selected_work_order_id
        )

        if serial_status.empty:
            st.info(
                "선택한 작업지시에 발급된 Serial이 없습니다."
            )

        else:
            # 선택한 작업지지의 전체 Serial 상태 구성
            show_serial_status_chart(
                serial_df=serial_status,
                work_order_no=selected_work_order_no,
            )

            st.divider()

            show_process_waiting_chart(
                serial_df=serial_status,
                work_order_no=selected_work_order_no,
            )

            st.divider()

            # 기존 Serial 상태 필터
            serial_status_options = [
                "전체",
                *sorted(
                    serial_status["status"]
                    .dropna()
                    .unique()
                    .tolist()
                ),
            ]

            selected_serial_status = st.selectbox(
                "Serial 상태",
                options=serial_status_options,
                key="production_serial_status_filter",
            )

            filtered_serial_status = serial_status.copy()

            if selected_serial_status != "전체":
                filtered_serial_status = filtered_serial_status[
                    filtered_serial_status["status"]
                    == selected_serial_status
                ]

            if filtered_serial_status.empty:
                st.warning(
                    "선택한 상태에 해당하는 Serial이 없습니다."
                )

            else:
                serial_display_dataframe = (
                    filtered_serial_status.rename(
                        columns={
                            "serial_no": "Serial 번호",
                            "status": "Serial 상태",
                            "started_at": "시작 시각",
                            "completed_at": "완료 시각",
                            "total_process_qty": "전체 공정 수",
                            "completed_process_qty": "완료 공정 수",
                            "process_progress_rate": "공정 진행률(%)",
                            "last_process_code": "최근 공정 코드",
                            "last_process_name": "최근 완료 공정",
                            "last_process_completed_at":
                                "최근 공정 완료 시각",
                            "next_process_code": "다음 공정 코드",
                            "next_process_name": "다음 진행 공정",
                        }
                    )
                )

                st.dataframe(
                    serial_display_dataframe[
                        [
                            "Serial 번호",
                            "Serial 상태",
                            "완료 공정 수",
                            "전체 공정 수",
                            "공정 진행률(%)",
                            "최근 완료 공정",
                            "다음 진행 공정",
                            "최근 공정 완료 시각",
                            "시작 시각",
                            "완료 시각",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                st.divider()
                st.subheader("Serial 공정 상세")

                serial_options = dict(
                    zip(
                        filtered_serial_status["serial_no"],
                        filtered_serial_status["product_serial_id"],
                    )
                )

                selected_serial_no = st.selectbox(
                    "상세 조회할 Serial",
                    options=list(serial_options.keys()),
                )

                selected_product_serial_id = serial_options[
                    selected_serial_no
                ]

                selected_serial_row = filtered_serial_status[
                    filtered_serial_status["product_serial_id"]
                    == selected_product_serial_id
                ].iloc[0]

                progress_rate = float(
                    selected_serial_row["process_progress_rate"]
                )

                st.write(
                    f"공정 진행률: "
                    f"{progress_rate:.1f}% "
                    f"({int(selected_serial_row['completed_process_qty'])}"
                    f"/{int(selected_serial_row['total_process_qty'])})"
                )

                st.progress(
                    min(max(progress_rate / 100.0, 0.0), 1.0)
                )

                serial_process_status = get_serial_process_status(
                    selected_product_serial_id
                )

                if serial_process_status.empty:
                    st.info("조회할 공정 정보가 없습니다.")

                else:
                    process_display_dataframe = serial_process_status.copy()

                    process_display_dataframe["process_status"] = (
                        process_display_dataframe["process_status"].map(
                            {
                                "NOT_STARTED": "대기",
                                "IN_PROGRESS": "진행 중",
                                "PASS": "합격",
                                "FAIL": "불합격",
                            }
                        )
                    )

                    process_display_dataframe["is_required"] = (
                        process_display_dataframe["is_required"].map(
                            {
                                1: "필수",
                                0: "선택",
                            }
                        )
                    )

                    process_display_dataframe = (
                        process_display_dataframe.rename(
                            columns={
                                "sequence_no": "순서",
                                "process_code": "공정 코드",
                                "process_name": "공정명",
                                "process_type": "공정 유형",
                                "is_required": "필수 여부",
                                "process_status": "진행 상태",
                                "result": "처리 결과",
                                "started_at": "시작 시각",
                                "completed_at": "완료 시각",
                                "remark": "비고",
                            }
                        )
                    )

                    st.dataframe(
                        process_display_dataframe[
                            [
                                "순서",
                                "공정 코드",
                                "공정명",
                                "공정 유형",
                                "필수 여부",
                                "진행 상태",
                                "처리 결과",
                                "시작 시각",
                                "완료 시각",
                                "비고",
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
