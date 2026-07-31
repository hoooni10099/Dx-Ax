from pathlib import Path
import shutil

import pytest

import src.db as db


PROJECT_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB_PATH = PROJECT_DIR / "sql" / "mes_dev.db"


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    mes_dev.db를 임시 DB로 복사하고,
    테스트 동안 src.db가 임시 DB를 사용하도록 변경한다.
    """
    if not SOURCE_DB_PATH.exists():
        raise FileNotFoundError(
            f"기준 데이터베이스를 찾을 수 없습니다: {SOURCE_DB_PATH}"
        )

    temporary_db_path = tmp_path / "mes_test.db"
    shutil.copy2(SOURCE_DB_PATH, temporary_db_path)

    monkeypatch.setattr(db, "DB_PATH", temporary_db_path)

    yield temporary_db_path
