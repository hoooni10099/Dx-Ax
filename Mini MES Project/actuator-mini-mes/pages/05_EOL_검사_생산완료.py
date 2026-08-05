from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.process_service import (
    complete_product,
    get_completion_ready_serials,
    get_eol_ready_serials,
    register_eol_test_result,
)

from src.ui import page_title, setup_page

from src.eol_service import (
    get_eol_current_trend,
    get_eol_operation_time_distribution,
    get_eol_result_summary,)

def show_eol_current_trend_chart(
    current_df: pd.DataFrame,
    current_limit_ma: float,
):
    """EOL 최대전류 추이와 허용 기준선을 표시한다."""

    st.subheader("최대전류 추이")

    if current_df.empty:
        st.info("표시할 EOL 검사 결과가 없습니다.")
        return

    chart_df = current_df.copy()

    chart_df["tested_at"] = pd.to_datetime(
        chart_df["tested_at"],
        errors="coerce",
    )

    chart_df["limit_status"] = chart_df["max_current_ma"].apply(
        lambda value: (
            "기준 초과"
            if value > current_limit_ma
            else "기준 이내"
        )
    )

    current_line = (
        alt.Chart(chart_df)
        .mark_line(
            color="#2563EB",
            strokeWidth=2,
        )
        .encode(
            x=alt.X(
                "tested_at:T",
                title="검사 일시",
            ),
            y=alt.Y(
                "max_current_ma:Q",
                title="최대전류 (mA)",
                scale=alt.Scale(zero=False),
            ),
            order=alt.Order("eol_test_result_id:Q"),
        )
    )

    current_points = (
        alt.Chart(chart_df)
        .mark_point(
            size=100,
            filled=True,
        )
        .encode(
            x=alt.X("tested_at:T"),
            y=alt.Y("max_current_ma:Q"),
            color=alt.Color(
                "limit_status:N",
                title="기준 판정",
                scale=alt.Scale(
                    domain=["기준 이내", "기준 초과"],
                    range=["#2563EB", "#DC2626"],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "tested_at:T",
                    title="검사 일시",
                    format="%Y-%m-%d %H:%M:%S",
                ),
                alt.Tooltip(
                    "serial_no:N",
                    title="Serial Number",
                ),
                alt.Tooltip(
                    "product_code:N",
                    title="제품",
                ),
                alt.Tooltip(
                    "work_order_no:N",
                    title="작업지시",
                ),
                alt.Tooltip(
                    "max_current_ma:Q",
                    title="최대전류",
                    format=".1f",
                ),
                alt.Tooltip(
                    "limit_status:N",
                    title="기준 판정",
                ),
                alt.Tooltip(
                    "result:N",
                    title="EOL 결과",
                ),
            ],
        )
    )

    limit_line = (
        alt.Chart(
            pd.DataFrame(
                {"current_limit_ma": [current_limit_ma]}
            )
        )
        .mark_rule(
            color="#DC2626",
            strokeDash=[6, 4],
            strokeWidth=2,
        )
        .encode(
            y=alt.Y("current_limit_ma:Q"),
            tooltip=[
                alt.Tooltip(
                    "current_limit_ma:Q",
                    title="허용 기준",
                    format=".1f",
                )
            ],
        )
    )

    chart = (
        current_line
        + current_points
        + limit_line
    ).properties(
        height=380,
    ).interactive()

    st.altair_chart(
        chart,
        width="stretch",
    )

    over_limit_count = int(
        (chart_df["max_current_ma"] > current_limit_ma).sum()
    )

    st.caption(
        f"임시 허용 기준: {current_limit_ma:,.1f}mA · "
        f"기준 초과: {over_limit_count:,}건"
    )

def reshape_operation_time_data(
    operation_time_df: pd.DataFrame,
) -> pd.DataFrame:
    """정·역방향 동작시간 컬럼을 박스플롯용 긴 형태로 변환한다."""

    if operation_time_df.empty:
        return pd.DataFrame()

    long_df = operation_time_df.melt(
        id_vars=[
            "eol_test_result_id",
            "tested_at",
            "result",
            "serial_no",
            "work_order_id",
            "work_order_no",
            "product_item_id",
            "product_code",
            "product_name",
        ],
        value_vars=[
            "forward_time_ms",
            "reverse_time_ms",
        ],
        var_name="direction_code",
        value_name="operation_time_ms",
    )

    long_df["direction"] = long_df["direction_code"].map(
        {
            "forward_time_ms": "정방향",
            "reverse_time_ms": "역방향",
        }
    )

    return long_df

def show_eol_operation_time_boxplot(
    operation_time_df: pd.DataFrame,
):
    """정·역방향 동작시간 분포를 박스플롯으로 표시한다."""

    st.subheader("정·역방향 동작시간 분포")

    if operation_time_df.empty:
        st.info("표시할 EOL 동작시간 데이터가 없습니다.")
        return

    chart_df = reshape_operation_time_data(operation_time_df)

    required_columns = {
        "direction",
        "operation_time_ms",
    }

    if not required_columns.issubset(chart_df.columns):
        st.error("동작시간 차트에 필요한 데이터 열이 없습니다.")
        return

    chart_df["operation_time_ms"] = pd.to_numeric(
        chart_df["operation_time_ms"],
        errors="coerce",
    )

    chart_df = chart_df.dropna(
        subset=[
            "direction",
            "operation_time_ms",
        ]
    )

    if chart_df.empty:
        st.info("표시할 유효한 EOL 동작시간 데이터가 없습니다.")
        return

    if "tested_at" in chart_df.columns:
        chart_df["tested_at"] = pd.to_datetime(
            chart_df["tested_at"],
            errors="coerce",
        )

    boxplot = (
        alt.Chart(chart_df)
        .mark_boxplot(
            extent=1.5,
            size=70,
        )
        .encode(
            x=alt.X(
                "direction:N",
                title=None,
                sort=["정방향", "역방향"],
            ),
            y=alt.Y(
                "operation_time_ms:Q",
                title="동작시간 (ms)",
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                "direction:N",
                title="동작 방향",
                scale=alt.Scale(
                    domain=["정방향", "역방향"],
                    range=["#2563EB", "#F59E0B"],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip(
                    "direction:N",
                    title="동작 방향",
                ),
                alt.Tooltip(
                    "operation_time_ms:Q",
                    title="동작시간",
                    format=",d",
                ),
            ],
        )
        .properties(
            height=380,
        )
    )

    st.altair_chart(
        boxplot,
        width="stretch",
    )

    forward_mean = chart_df.loc[
        chart_df["direction"] == "정방향",
        "operation_time_ms",
    ].mean()

    reverse_mean = chart_df.loc[
        chart_df["direction"] == "역방향",
        "operation_time_ms",
    ].mean()

    forward_mean_text = (
        f"{forward_mean:,.1f}ms"
        if pd.notna(forward_mean)
        else "데이터 없음"
    )

    reverse_mean_text = (
        f"{reverse_mean:,.1f}ms"
        if pd.notna(reverse_mean)
        else "데이터 없음"
    )

    st.caption(
        f"정방향 평균: {forward_mean_text} · "
        f"역방향 평균: {reverse_mean_text} · "
        f"검사 표본: {len(operation_time_df):,}건"
    )

def show_eol_result_summary(
    product_item_id: int,
):
    """선택한 제품의 EOL 검사 결과 요약을 표시한다."""

    try:
        summary_df = get_eol_result_summary(
            product_item_id=product_item_id,
        )
    except Exception as error:
        st.error("EOL 검사 결과 요약을 불러오지 못했습니다.")
        st.caption(f"오류 내용: {error}")
        return

    if summary_df.empty:
        st.info("선택한 제품의 EOL 검사 결과가 없습니다.")
        return

    summary = summary_df.iloc[0]

    total_count = (
        0
        if pd.isna(summary["total_count"])
        else int(summary["total_count"])
    )

    pass_count = (
        0
        if pd.isna(summary["pass_count"])
        else int(summary["pass_count"])
    )

    fail_count = (
        0
        if pd.isna(summary["fail_count"])
        else int(summary["fail_count"])
    )

    pass_rate = (
        pass_count / total_count * 100
        if total_count > 0
        else 0.0
    )

    st.subheader("검사 결과 요약")

    total_column, pass_column, fail_column, rate_column = (
        st.columns(4)
    )

    total_column.metric(
        "전체 검사",
        f"{total_count:,}건",
    )

    pass_column.metric(
        "합격",
        f"{pass_count:,}건",
    )

    fail_column.metric(
        "불합격",
        f"{fail_count:,}건",
    )

    rate_column.metric(
        "합격률",
        f"{pass_rate:.1f}%",
    )

def show_eol_monitoring():
    """EOL 전류 및 동작시간 모니터링 영역을 표시한다."""

    try:
        all_df = get_eol_current_trend()
    except Exception as error:
        st.error("EOL 품질 모니터링 데이터를 불러오지 못했습니다.")
        st.caption(f"오류 내용: {error}")
        return

    if all_df.empty:
        st.info("표시할 EOL 품질 모니터링 데이터가 없습니다.")
        return

    st.subheader("EOL 품질 모니터링")

    if all_df.empty:
        st.info("등록된 EOL 검사 결과가 없습니다.")
        return

    product_options = (
        all_df[
            [
                "product_item_id",
                "product_code",
                "product_name",
            ]
        ]
        .drop_duplicates()
        .sort_values("product_code")
    )

    product_labels = {
        int(row["product_item_id"]): (
            f"{row['product_code']} - {row['product_name']}"
        )
        for _, row in product_options.iterrows()
    }

    filter_column, limit_column = st.columns(2)

    with filter_column:
        selected_product_id = st.selectbox(
            "제품",
            options=list(product_labels),
            format_func=lambda item_id: product_labels[item_id],
        )

    with limit_column:
        current_limit_ma = st.number_input(
            "최대 허용 전류 (mA)",
            min_value=0.0,
            value=1500.0,
            step=10.0,
            help="현재는 임시 분석 기준이며 DB에 저장되지 않습니다.",
        )

    show_eol_result_summary(
        product_item_id=selected_product_id,
    )

    st.divider()

    # 같은 제품의 동작시간 데이터 조회
    try:
        operation_time_df = get_eol_operation_time_distribution(
            product_item_id=selected_product_id,
        )
    except Exception as error:
        st.error("EOL 동작시간 분포를 불러오지 못했습니다.")
        st.caption(f"오류 내용: {error}")
    else:
        if operation_time_df.empty:
            st.info("선택한 제품의 동작시간 데이터가 없습니다.")
        else:
            show_eol_operation_time_boxplot(
                operation_time_df=operation_time_df,
            )

    st.divider()

    # 이미 조회한 전체 데이터에서 선택한 제품만 필터링
    current_df = all_df.loc[
        all_df["product_item_id"] == selected_product_id
    ].copy()

    show_eol_current_trend_chart(
        current_df=current_df,
        current_limit_ma=current_limit_ma,
    )


setup_page("EOL 검사 및 생산 완료")

page_title(
    title="EOL 검사 및 생산 완료",
)

st.subheader("1. EOL 검사 결과 등록")
eol_result_message = st.session_state.get(
    "eol_result_message"
)

if eol_result_message is not None:
    st.markdown(
        "#### 최근 EOL 검사 결과 "
        f"— {eol_result_message['serial_no']}"
    )
    if eol_result_message["result"] == "PASS":
        st.success(
            "EOL 검사 결과가 PASS로 등록되었습니다. "
            "이제 생산 완료 처리가 가능합니다."
        )
    else:
        st.error(
            "EOL 검사 결과가 FAIL로 등록되었습니다."
        )

    result_column1, result_column2 = st.columns(2)

    with result_column1:
        st.metric(
            "최종 판정",
            eol_result_message["result"],
        )

    with result_column2:
        position_error = eol_result_message[
            "position_error_deg"
        ]

        st.metric(
            "위치 오차",
            (
                f"{position_error:.1f}°"
                if position_error is not None
                else "검사 대상 아님"
            ),
        )

    if eol_result_message["failure_reason"]:
        st.warning(
            "불합격 사유: "
            f"{eol_result_message['failure_reason']}"
        )

    if st.button(
        "검사 결과 확인 완료",
        key="clear_eol_result_message",
    ):
        del st.session_state["eol_result_message"]
        st.rerun()

try:
    eol_ready_serials = get_eol_ready_serials()
except Exception as error:
    eol_ready_serials = pd.DataFrame()
    eol_ready_serials_load_failed = True

    st.error("EOL 검사 대상 목록을 불러오지 못했습니다.")
    st.caption(f"오류 내용: {error}")
else:
    eol_ready_serials_load_failed = False

if eol_ready_serials_load_failed:
    pass

elif eol_ready_serials.empty:
    st.info(
        "현재 EOL 검사를 등록할 수 있는 제품 Serial이 없습니다."
    )

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

            st.session_state["eol_result_message"] = {
                "serial_no": selected_serial["serial_no"],
                "result": result,
                "forward_ok": forward_ok,
                "reverse_ok": reverse_ok,
                "forward_time_ms": int(forward_time_ms),
                "reverse_time_ms": int(reverse_time_ms),
                "max_current_ma": float(max_current_ma),
                "position_error_deg": position_error_deg,
                "failure_reason": failure_reason,
            }

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

try:
    completion_ready_serials = get_completion_ready_serials()
except Exception as error:
    completion_ready_serials = pd.DataFrame()
    completion_ready_serials_load_failed = True

    st.error("생산 완료 대상 목록을 불러오지 못했습니다.")
    st.caption(f"오류 내용: {error}")
else:
    completion_ready_serials_load_failed = False

if completion_ready_serials_load_failed:
    pass

elif completion_ready_serials.empty:
    st.info("현재 생산 완료 처리할 제품 Serial이 없습니다.")

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
            service_result = complete_product(
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

        except Exception as error:
            st.error(
                "생산 완료 처리 중 오류가 발생했습니다. "
                "잠시 후 다시 시도해 주세요."
            )
            st.caption(f"오류 내용: {error}")

        else:
            if service_result.success:
                st.session_state["completion_success_message"] = (
                    service_result.message
                )
                st.rerun()
            else:
                st.error(service_result.message)

st.divider()

show_eol_monitoring()
