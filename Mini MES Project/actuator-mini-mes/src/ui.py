from __future__ import annotations

import sqlite3
import pandas as pd
import streamlit as st

from src.db import DB_PATH, database_exists


# 브라우저 제목과 화면 너비 설정
def setup_page (title: str) -> None:
    st.set_page_config(
        page_title = f"Actuator Mini MES - {title}",
        layout = "wide",
    )

# 페이지 제목과 학습 안내 표시
def page_title (
        title : str,
        description : str,
        tables : str,
        task : str,
) -> None:
    st.title(title)

    st.info (
        f"""
        이 화면에서 배우는 내용 : {description}

        관련 테이블 {tables}

        수행할 작업 : {task}
        """
    )

# 현재 DB 파일 존재 여부 표시
def show_database_status() -> None:
    if database_exists():
        st.success(f"데이터베이스 연결 대상 : {DB_PATH}")
    else:
        st.error(f"데이터베이스 파일을 찾을 수 없습니다 : {DB_PATH}")

# 조회 결과 DataFrame 표시
def show_dataframe (
        df: pd.DataFrame,
        empty_message : str = "조건에 해당하는 데이터가 없습니다.",
) -> None:
    if df.empty:
        st.warning(empty_message)
        return

    st.dataframe(
        df,
        use_container_width = True,
        hide_index = True,
    )

# 대시보드 지표를 가로로 표시
def metric_row (values : list[tuple[str, object]]) -> None:
    columns = st.columns(len(values))

    for column, (label, value) in zip(columns, values):
        column.metric(label, value)

# SQLite 조회 결과 한 행을 딕셔너리로 변환
def row_to_dict (row : sqlite3.Row | None) -> dict:
    if row is None:
        return {}

    return dict(row)
