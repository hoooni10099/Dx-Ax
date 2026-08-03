from __future__ import annotations

import streamlit as st
import altair as alt
import pandas as pd

from src.ui import show_database_status

from src.dashboard_service import (
    get_current_process_counts,
    get_daily_production,
    get_quality_result_counts,
    get_work_order_progress,
)

from src.material_lot_service import (
    get_available_stock_by_material,
    get_material_inventory_metrics,
)

def show_dashboard_charts():
    work_order_df = get_work_order_progress()
    process_df = get_current_process_counts()
    daily_df = get_daily_production()
    quality_df = get_quality_result_counts()

    left_column, right_column = st.columns([2, 1])

    with left_column:
        show_work_order_progress_chart(work_order_df)

    with right_column:
        show_quality_chart(quality_df)

    left_column, right_column = st.columns(2)

    with left_column:
        show_current_process_chart(process_df)

    with right_column:
        show_daily_production_chart(daily_df)

def show_work_order_progress_chart(df: pd.DataFrame):
    st.subheader("작업지시별 계획 대비 완료")

    if df.empty:
        st.info("표시할 작업지시가 없습니다.")
        return

    chart_df = df.melt(
        id_vars=[
            "work_order_no",
            "item_name",
        ],
        value_vars=[
            "planned_qty",
            "completed_qty",
        ],
        var_name="quantity_type",
        value_name="quantity",
    )

    chart_df["quantity_type"] = chart_df["quantity_type"].map(
        {
            "planned_qty": "계획",
            "completed_qty": "완료",
        }
    )

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "quantity:Q",
                title="수량",
                axis=alt.Axis(tickMinStep=1),
            ),
            y=alt.Y(
                "work_order_no:N",
                title=None,
                sort=None,
            ),
            color=alt.Color(
                "quantity_type:N",
                title="구분",
                scale=alt.Scale(
                    domain=["계획", "완료"],
                    range=["#CBD5E1", "#2563EB"],
                ),
            ),
            yOffset="quantity_type:N",
            tooltip=[
                alt.Tooltip(
                    "work_order_no:N",
                    title="작업지시",
                ),
                alt.Tooltip(
                    "item_name:N",
                    title="제품",
                ),
                alt.Tooltip(
                    "quantity_type:N",
                    title="구분",
                ),
                alt.Tooltip(
                    "quantity:Q",
                    title="수량",
                ),
            ],
        )
        .properties(height=280)
    )

    st.altair_chart(chart, width="stretch")

def show_quality_chart(df: pd.DataFrame):
    st.subheader("합격·불합격")

    all_results = pd.DataFrame(
        {
            "result_name": ["합격", "불합격"],
        }
    )

    chart_df = all_results.merge(
        df,
        on="result_name",
        how="left",
    )

    chart_df["result_qty"] = (
        chart_df["result_qty"]
        .fillna(0)
        .astype(int)
    )

    total_qty = int(chart_df["result_qty"].sum())
    pass_qty = int(
        chart_df.loc[
            chart_df["result_name"] == "합격",
            "result_qty",
        ].sum()
    )

    if total_qty == 0:
        st.info("완료된 검사 결과가 없습니다.")
        return

    pass_rate = pass_qty / total_qty * 100

    chart = (
        alt.Chart(chart_df)
        .mark_arc(innerRadius=55, outerRadius=85)
        .encode(
            theta=alt.Theta(
                "result_qty:Q",
                stack=True,
            ),
            color=alt.Color(
                "result_name:N",
                title="판정",
                scale=alt.Scale(
                    domain=["합격", "불합격"],
                    range=["#16A34A", "#DC2626"],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "result_name:N",
                    title="판정",
                ),
                alt.Tooltip(
                    "result_qty:Q",
                    title="수량",
                ),
            ],
        )
        .properties(height=250)
    )

    st.altair_chart(chart, width="stretch")
    st.caption(
        f"총 {total_qty}개 · 합격률 {pass_rate:.1f}%"
    )

def show_current_process_chart(df: pd.DataFrame):
    st.subheader("공정별 현재 제품 수량")

    if df.empty:
        st.info("현재 공정 대기 중인 제품이 없습니다.")
        return

    chart = (
        alt.Chart(df)
        .mark_bar(
            color="#F59E0B",
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4,
        )
        .encode(
            x=alt.X(
                "process_name:N",
                title=None,
                sort=alt.EncodingSortField(
                    field="sequence_no",
                    order="ascending",
                ),
            ),
            y=alt.Y(
                "product_qty:Q",
                title="제품 수량",
                axis=alt.Axis(tickMinStep=1),
            ),
            tooltip=[
                alt.Tooltip(
                    "process_name:N",
                    title="공정",
                ),
                alt.Tooltip(
                    "product_qty:Q",
                    title="수량",
                ),
            ],
        )
        .properties(height=280)
    )

    st.altair_chart(chart, width="stretch")

def show_daily_production_chart(df: pd.DataFrame):
    st.subheader("최근 7일 생산량")

    if df.empty:
        st.info("최근 생산실적이 없습니다.")
        return

    chart_df = df.copy()
    chart_df["production_date"] = pd.to_datetime(
        chart_df["production_date"]
    )

    line = (
        alt.Chart(chart_df)
        .mark_line(
            color="#2563EB",
            point=True,
            strokeWidth=3,
        )
        .encode(
            x=alt.X(
                "production_date:T",
                title=None,
                axis=alt.Axis(format="%m-%d"),
            ),
            y=alt.Y(
                "production_qty:Q",
                title="생산 수량",
                axis=alt.Axis(tickMinStep=1),
            ),
            tooltip=[
                alt.Tooltip(
                    "production_date:T",
                    title="생산일",
                    format="%Y-%m-%d",
                ),
                alt.Tooltip(
                    "production_qty:Q",
                    title="생산량",
                ),
            ],
        )
    )

    st.altair_chart(
        line.properties(height=280),
        width="stretch",
    )


st.set_page_config(
    page_title="Actuator Mini MES",
    page_icon = ":gear:",
    layout="wide",
    initial_sidebar_state = "expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .main-title {
            font-size: 2.7rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }

        .main-description {
            color: #64748b;
            font-size: 1.05rem;
            margin-bottom: 1.8rem;
        }

        .hero-box {
            padding: 1.8rem 2rem;
            border: 1px solid #dbeafe;
            border-radius: 16px;
            background: linear-gradient(
                135deg,
                #f8fafc 0%,
                #eff6ff 100%
            );
            margin-bottom: 1.5rem;
            color: #1e293b;
        }

        .hero-box h3 {
            color: #0f172a;
            margin-top: 0;
            margin-bottom: 0.7rem;
        }

        .hero-box p {
            color: #475569;
            margin-bottom: 0;
            line-height: 1.7;
        }

        .feature-card {
            min-height: 210px;
            padding: 1.3rem;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            background-color: #ffffff;
            color: #1e293b;
        }

        .feature-card h4 {
            color: #0f172a;
            margin-top: 0;
            margin-bottom: 0.6rem;
            font-size: 1.15rem;
            font-weight: 700;
        }

        .feature-card p {
            color: #475569;
            line-height: 1.7;
            margin-bottom: 0;
        }

        .flow-box {
            min-height: 120px;
            padding: 1.2rem 0.8rem;
            border: 1px solid transparent;
            border-radius: 12px;

            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;

            color: #1e293b;
            text-align: center;
            font-weight: 700;
            line-height: 1.5;
            word-break: keep-all;
        }

        .flow-box .step-label {
            font-size: 0.85rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }

        .flow-box .step-name {
            color: #1e293b;
            font-size: 1rem;
            font-weight: 700;
        }

        .flow-step-1 {
            background-color: #eff6ff;
            border-color: #bfdbfe;
        }

        .flow-step-2 {
            background-color: #eef2ff;
            border-color: #c7d2fe;
        }

        .flow-step-3 {
            background-color: #f0fdfa;
            border-color: #99f6e4;
        }

        .flow-step-4 {
            background-color: #fff7ed;
            border-color: #fed7aa;
        }

        .flow-step-5 {
            background-color: #f0fdf4;
            border-color: #bbf7d0;
        }
    </style>
    """, unsafe_allow_html = True,
)

st.markdown(
    '<div class = "main-title"> 🏭Actuator Mini MES</div>',
    unsafe_allow_html = True,
)

st.markdown(
    """
    <div class = "main-description">
        자동차용 소형 전동 액추에이터의 생산 과정을 관리하고
        추적하는 학습용 Mini MES입니다.
    </div>
    """,
    unsafe_allow_html = True,
)

show_database_status()

st.markdown(
    """
    <div class="hero-box">
        <h3>생산 현장의 흐름을 하나의 시스템으로 연결합니다</h3>
        <p>
            자재 LOT 입고부터 작업지시, 완제품 Serial 발급,
            공정 작업실적, EOL 검사, 생산 완료 및 추적성 조회까지
            전체 생산 흐름을 단계별로 관리할 수 있습니다.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("주요 기능")

column1, column2, column3 = st.columns(3)

with column1:
    st.markdown(
        """
        <div class="feature-card">
            <h4>📦 생산 준비</h4>
            <p>
                품목·BOM·공정 기준정보를 확인하고,
                생산에 필요한 자재 LOT와 작업지시를 등록합니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with column2:
    st.markdown(
        """
        <div class="feature-card">
            <h4>⚙️ 생산 실행</h4>
            <p>
                완제품 Serial을 발급하고 공정 순서에 따라
                작업실적과 자재 투입 이력을 등록합니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with column3:
    st.markdown(
        """
        <div class="feature-card">
            <h4>🔍 검사 및 추적</h4>
            <p>
                EOL 검사와 생산 완료 처리를 수행하고
                Serial과 자재 LOT를 양방향으로 추적합니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.subheader("전체 생산 흐름")

flow_columns = st.columns(5)

flow_steps = [
    ("1", "자재 LOT 입고", "#2563eb"),
    ("2", "작업지시·Serial", "#0f05db"),
    ("3", "공정 작업", "#0f766e"),
    ("4", "EOL 검사", "#c2410c"),
    ("5", "생산 완료·추적", "#15803d"),
]

for column, (step_number, step_name, step_color) in zip(
    flow_columns,
    flow_steps,
):
    with column:
        st.markdown(
            f"""
            <div class="flow-box flow-step-{step_number}">
                <div style="
                    color: {step_color};
                    font-size: 0.85rem;
                    font-weight: 700;
                    margin-bottom: 0.4rem;
                ">
                    STEP {step_number}
                </div>
                <div>{step_name}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

guide_column, status_column = st.columns([2, 1])

st.title("Mini MES 대시보드")
st.caption("작업지시, 공정 진행 및 생산실적을 확인합니다.")

show_dashboard_charts()
