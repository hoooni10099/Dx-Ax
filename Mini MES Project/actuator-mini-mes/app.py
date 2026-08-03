from __future__ import annotations

import streamlit as st

from src.ui import show_database_status

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

with guide_column:
    st.subheader("시작 방법")

    st.markdown(
        """
        1. 왼쪽 사이드바에서 사용할 화면을 선택합니다.
        2. 자재 LOT와 작업지시를 등록합니다.
        3. Serial을 발급하고 공정 순서대로 생산을 진행합니다.
        4. EOL 검사와 생산 완료 처리를 수행합니다.
        5. 정방향·역방향 추적 화면에서 생산 이력을 확인합니다.
        """
    )

with status_column:
    st.subheader("구현 범위")

    st.success("1차 Mini MES 생산 사이클 구현 완료")

    st.markdown(
        """
        - 기준정보 조회
        - 자재 LOT 관리
        - 작업지시 및 Serial 관리
        - 공정 작업실적 등록
        - EOL 검사 및 생산 완료
        - 정방향·역방향 추적
        """
    )

st.caption(
    "Actuator Mini MES · Python · SQLite · Streamlit"
)
