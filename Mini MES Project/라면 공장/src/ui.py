import pandas as pd
import streamlit as st

#page_config를 제목 함수로 수정
def setup_page(title):
    st.set_page_config(page_title = 'Mini MES app2.py')

#page_title을 개량한 커스텀 함수
def page_title(title: str, description: str, tables: str, task: str):
    st.title(title)
    st.info(
        f"""
        이 화면에서 배우는 내용: {description}

        관련 테이블: {tables}

        학생이 수행할 작업: {task}
        """
    )
