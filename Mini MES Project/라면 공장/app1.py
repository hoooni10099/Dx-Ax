import streamlit as st
import sqlite3
import pandas as pd

from src.ui import setup_page, page_title


# conn = sqlite3.connect('./sql/mini_mes.db')

setup_page("MINI MES app2.py")

page_title(
    "Mini MES 교육 앱",
    "MES의 기본 개념과 품목, LOT, 생산실적, 원자재 투입 이력의 관계를 확인합니다.",
    "item, lot, production, production_material",
    "DB 연결 상태와 테이블 구성을 확인한 뒤 왼쪽 메뉴에서 실습 화면으로 이동합니다.",
)

# show_database_status()
