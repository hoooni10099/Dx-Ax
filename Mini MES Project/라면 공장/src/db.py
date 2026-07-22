from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent # mes 폴더(조절해서 맞춰)
DB_PATH = BASE_DIR/'sql'/'mini_mes.db'

def database_exists() -> bool: #  DB 파일이 존재하는지 확인
    return DB_PATH.exists()

def get_connection() -> sqlite3.Connection: # DB 연결 생성
    if not database_exists():
        raise FileNotFoundError(f"SQLite 데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row # 컬럼명으로 접근 가능
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def fetch_dataframe(sql: str, params: tuple = ()) -> pd.DataFrame: # DataFrame으로 조회
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params = params)
    
def fetch_one(sql: str, params: tuple = ()) -> sqlite3.Row | None: # 한 행 조회
    with get_connection() as connection:
        cursor = connection.execute(sql, params)
        return cursor.fetchone()


def fetch_all(sql: str, params: tuple = ()) -> list[sqlite3.Row]: # 여러 행 조회
    with get_connection() as connection:
        cursor = connection.execute(sql, params)
        return cursor.fetchall()
