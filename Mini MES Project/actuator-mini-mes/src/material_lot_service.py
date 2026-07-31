from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.db import get_connection

# 02_자재_LOT_관리.py

@dataclass
class ServiceResult:
    success: bool
    message: str

def get_material_lots(
    material_item_id: int | None = None,
    status: str | None = None,
    keyword: str = "",
    received_date_from: str | None = None,
    received_date_to: str | None = None,
) -> pd.DataFrame:
    sql = """
        SELECT
            material_lot.lot_no AS "LOT번호",
            item.item_code AS "자재코드",
            item.item_name AS "자재명",
            material_lot.received_qty AS "입고수량",
            material_lot.received_date AS "입고일",
            CASE material_lot.status
                WHEN 'AVAILABLE' THEN '사용 가능'
                WHEN 'EXHAUSTED' THEN '소진'
                WHEN 'BLOCKED' THEN '사용 차단'
                ELSE material_lot.status
            END AS "상태",
            material_lot.created_at AS "등록일시"
        FROM material_lot
        JOIN item
          ON item.item_id = material_lot.material_item_id
        WHERE 1 = 1
    """

    params: list[object] = []

    if material_item_id is not None:
        sql += """
            AND material_lot.material_item_id = ?
        """
        params.append(material_item_id)

    if status is not None:
        sql += """
            AND material_lot.status = ?
        """
        params.append(status)

    keyword = keyword.strip()

    if keyword:
        sql += """
            AND material_lot.lot_no LIKE ?
        """
        params.append(f"%{keyword}%")

    if received_date_from is not None:
        sql += """
            AND material_lot.received_date >= ?
        """
        params.append(received_date_from)

    if received_date_to is not None:
        sql += """
            AND material_lot.received_date <= ?
        """
        params.append(received_date_to)

    sql += """
        ORDER BY
            material_lot.received_date DESC,
            material_lot.lot_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )

def create_material_lot(
    lot_no: str,
    material_item_id: int,
    received_qty: int,
    received_date: str,
) -> ServiceResult:
    lot_no = lot_no.strip().upper()
    received_date = received_date.strip()

    # 1. LOT 번호 검증
    if not lot_no:
        return ServiceResult(
            success=False,
            message="LOT 번호를 입력해주세요.",
        )

    # 2. 자재 ID 검증
    if material_item_id <= 0:
        return ServiceResult(
            success=False,
            message="올바른 자재를 선택해주세요.",
        )

    # 3. 입고 수량 검증
    if received_qty <= 0:
        return ServiceResult(
            success=False,
            message="입고 수량은 1개 이상이어야 합니다.",
        )

    # 4. 입고일 형식 및 미래 날짜 검증
    try:
        parsed_received_date = date.fromisoformat(received_date)
    except ValueError:
        return ServiceResult(
            success=False,
            message="입고일은 YYYY-MM-DD 형식이어야 합니다.",
        )

    if parsed_received_date > date.today():
        return ServiceResult(
            success=False,
            message="입고일은 오늘 이후 날짜로 등록할 수 없습니다.",
        )

    try:
        with get_connection() as connection:
            # 5. 선택한 품목이 활성 자재인지 확인
            material = connection.execute(
                """
                SELECT
                    item_code,
                    item_name
                FROM item
                WHERE item_id = ?
                  AND item_type = 'MATERIAL'
                  AND is_active = 1
                """,
                (material_item_id,),
            ).fetchone()

            if material is None:
                return ServiceResult(
                    success=False,
                    message="선택한 자재가 존재하지 않거나 비활성 상태입니다.",
                )

            # 6. LOT 번호 중복 확인
            duplicate = connection.execute(
                """
                SELECT 1
                FROM material_lot
                WHERE lot_no = ?
                """,
                (lot_no,),
            ).fetchone()

            if duplicate is not None:
                return ServiceResult(
                    success=False,
                    message=f"이미 등록된 LOT 번호입니다: {lot_no}",
                )

            # 7. 신규 LOT 등록
            connection.execute(
                """
                INSERT INTO material_lot (
                    lot_no,
                    material_item_id,
                    received_qty,
                    received_date,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, 'AVAILABLE', CURRENT_TIMESTAMP)
                """,
                (
                    lot_no,
                    material_item_id,
                    received_qty,
                    received_date,
                ),
            )

            connection.commit()

    except sqlite3.Error as error:
        return ServiceResult(
            success=False,
            message=f"자재 LOT 등록 중 데이터베이스 오류가 발생했습니다: {error}",
        )

    return ServiceResult(
        success=True,
        message=(
            f"{material['item_code']} - {material['item_name']}의 "
            f"LOT {lot_no}가 등록되었습니다."
        ),
    )
