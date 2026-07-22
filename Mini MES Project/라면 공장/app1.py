import streamlit as st
import sqlite3
import pandas as pd

from src.db import database_exists, fetch_one, fetch_all, fetch_dataframe
from src import queries
from src.ui import setup_page, page_title, show_database_status, DB_PATH, metric_row, show_dataframe

setup_page("MES")
page_title("Mini MES 메소드 테스트","","","")

if database_exists():
    print("DB 있음")
else:
    print("DB 없음")

#DB파일 연결여부 상태조회
show_database_status()

st.subheader("Streamlit Test")
st.markdown(
    """
    # 제목1
    ## 제목2
    ### 제목3
    - 내용1
    - 내용2
    """
)

try:
    counts = queries.table_counts()
    count_map = dict(zip(counts["table_name"], counts["row_count"]))

    metric_row(
            [
                ("품목 수", count_map.get("item", 0)),
                ("LOT 수", count_map.get("lot", 0)),
                ("생산실적 수", count_map.get("production", 0)),
                ("원자재 투입 행 수", count_map.get("production_material", 0)),
            ]
        )

    # 품목 목록
    df = fetch_dataframe("""
    SELECT *
    FROM lot
    """)
    st.dataframe(df)


    # 품목 상세
    Item = fetch_one("""
    SELECT *
    FROM item
    WHERE item_code=?
    """, ("FG-RAMEN-001",))
    print(Item["item_name"])


    rows = fetch_all(
    "SELECT * FROM item"
    )
    for row in rows:
        print(row["item_name"])


    print(counts)
    st.write(counts)
    st.write(counts["table_name"])
    st.write(counts["row_count"])
    st.write(dict(zip(counts["table_name"], counts["row_count"])))


except Exception as exc:
    st.error("데이터베이스 구조를 확인하는 중 오류가 발생했습니다.")
    st.exception(exc)




