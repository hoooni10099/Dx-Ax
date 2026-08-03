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
    keyword = (keyword or "").strip()
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
                WHEN 'BLOCKED' THEN '사용 중지'
                ELSE material_lot.status
            END AS "상태",
            material_lot.blocked_reason AS "사용중지사유",
            material_lot.blocked_at AS "사용중지일시",
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
                VALUES (?, ?, ?, ?, 'AVAILABLE', datetime('now', 'localtime'))
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

def get_active_materials() -> pd.DataFrame:
    sql = """
        SELECT
            item_id,
            item_code,
            item_name
        FROM item
        WHERE item_type = 'MATERIAL'
          AND is_active = 1
        ORDER BY item_code
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def block_material_lot(
    material_lot_id: int,
    blocked_reason: str,
) -> ServiceResult:
    """사용 가능한 자재 LOT을 사용 중지한다."""

    try:
        material_lot_id = int(material_lot_id)
    except (TypeError, ValueError):
        return ServiceResult(
            success=False,
            message="LOT 선택값이 올바르지 않습니다.",
        )

    if material_lot_id <= 0:
        return ServiceResult(
            success=False,
            message="LOT 선택값이 올바르지 않습니다.",
        )

    blocked_reason = str(blocked_reason or "").strip()

    if not blocked_reason:
        return ServiceResult(
            success=False,
            message="사용 중지 사유를 입력해주세요.",
        )

    if len(blocked_reason) > 500:
        return ServiceResult(
            success=False,
            message="사용 중지 사유는 500자 이하로 입력해주세요.",
        )

    try:
        with get_connection() as connection:
            lot = connection.execute(
                """
                SELECT
                    ml.lot_no,
                    ml.status,
                    ml.received_qty
                        - COALESCE(SUM(mc.consumed_qty), 0)
                        AS remaining_qty
                FROM material_lot AS ml
                LEFT JOIN material_consumption AS mc
                  ON mc.material_lot_id = ml.material_lot_id
                WHERE ml.material_lot_id = ?
                GROUP BY
                    ml.material_lot_id,
                    ml.lot_no,
                    ml.status,
                    ml.received_qty
                """,
                (material_lot_id,),
            ).fetchone()

            if lot is None:
                return ServiceResult(
                    success=False,
                    message="선택한 자재 LOT을 찾을 수 없습니다.",
                )

            if lot["status"] == "BLOCKED":
                return ServiceResult(
                    success=False,
                    message="이미 사용 중지된 LOT입니다.",
                )

            if lot["status"] == "EXHAUSTED":
                return ServiceResult(
                    success=False,
                    message="소진된 LOT은 사용 중지할 수 없습니다.",
                )

            if lot["status"] != "AVAILABLE":
                return ServiceResult(
                    success=False,
                    message="현재 상태에서는 LOT을 사용 중지할 수 없습니다.",
                )

            if lot["remaining_qty"] <= 0:
                return ServiceResult(
                    success=False,
                    message="잔여 수량이 없는 LOT은 사용 중지할 수 없습니다.",
                )

            cursor = connection.execute(
                """
                UPDATE material_lot
                SET
                    status = 'BLOCKED',
                    blocked_reason = ?,
                    blocked_at = datetime('now', 'localtime')
                WHERE material_lot_id = ?
                  AND status = 'AVAILABLE'
                """,
                (
                    blocked_reason,
                    material_lot_id,
                ),
            )

            if cursor.rowcount != 1:
                return ServiceResult(
                    success=False,
                    message="LOT 상태가 변경되어 사용 중지하지 못했습니다.",
                )

            connection.commit()

    except sqlite3.Error as error:
        return ServiceResult(
            success=False,
            message=(
                "LOT 사용 중지 처리 중 데이터베이스 오류가 "
                f"발생했습니다: {error}"
            ),
        )

    return ServiceResult(
        success=True,
        message=f"LOT {lot['lot_no']}을 사용 중지했습니다.",
    )

def get_status_changeable_material_lots() -> pd.DataFrame:
    sql = """
        SELECT
            ml.material_lot_id,
            ml.lot_no,
            i.item_code,
            i.item_name,
            ml.status,
            ml.received_qty
                - COALESCE(SUM(mc.consumed_qty), 0)
                AS remaining_qty
        FROM material_lot AS ml
        JOIN item AS i
          ON i.item_id = ml.material_item_id
        LEFT JOIN material_consumption AS mc
          ON mc.material_lot_id = ml.material_lot_id
        WHERE ml.status IN ('AVAILABLE')
        GROUP BY
            ml.material_lot_id,
            ml.lot_no,
            i.item_code,
            i.item_name,
            ml.status,
            ml.received_qty
        ORDER BY
            ml.received_date DESC,
            ml.lot_no
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def get_material_inventory_metrics() -> dict:
    """자재 LOT 페이지 상단의 핵심 재고 지표를 조회한다."""

    sql = """
        WITH lot_consumption AS (
            SELECT
                material_lot_id,
                SUM(consumed_qty) AS consumed_qty
            FROM material_consumption
            GROUP BY material_lot_id
        ),
        lot_inventory AS (
            SELECT
                ml.material_lot_id,
                ml.status,
                MAX(
                    ml.received_qty
                    - COALESCE(lc.consumed_qty, 0),
                    0
                ) AS remaining_qty
            FROM material_lot AS ml
            LEFT JOIN lot_consumption AS lc
              ON lc.material_lot_id = ml.material_lot_id
        )
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'AVAILABLE'
                        THEN remaining_qty
                        ELSE 0
                    END
                ),
                0
            ) AS available_stock_qty,
            SUM(
                CASE
                    WHEN status = 'AVAILABLE' THEN 1
                    ELSE 0
                END
            ) AS available_lot_count,
            SUM(
                CASE
                    WHEN status = 'BLOCKED' THEN 1
                    ELSE 0
                END
            ) AS blocked_lot_count,
            SUM(
                CASE
                    WHEN status = 'EXHAUSTED' THEN 1
                    ELSE 0
                END
            ) AS exhausted_lot_count
        FROM lot_inventory
    """

    with get_connection() as connection:
        row = connection.execute(sql).fetchone()

    return {
        "available_stock_qty": int(row["available_stock_qty"] or 0),
        "available_lot_count": int(row["available_lot_count"] or 0),
        "blocked_lot_count": int(row["blocked_lot_count"] or 0),
        "exhausted_lot_count": int(row["exhausted_lot_count"] or 0),
    }

def get_available_stock_by_material() -> pd.DataFrame:
    """AVAILABLE LOT의 잔여수량을 자재별로 집계한다."""

    sql = """
        WITH lot_consumption AS (
            SELECT
                material_lot_id,
                SUM(consumed_qty) AS consumed_qty
            FROM material_consumption
            GROUP BY material_lot_id
        ),
        available_inventory AS (
            SELECT
                ml.material_item_id,
                MAX(
                    ml.received_qty
                    - COALESCE(lc.consumed_qty, 0),
                    0
                ) AS remaining_qty
            FROM material_lot AS ml
            LEFT JOIN lot_consumption AS lc
              ON lc.material_lot_id = ml.material_lot_id
            WHERE ml.status = 'AVAILABLE'
        )
        SELECT
            i.item_code,
            i.item_name,
            COALESCE(
                SUM(ai.remaining_qty),
                0
            ) AS available_qty
        FROM item AS i
        LEFT JOIN available_inventory AS ai
          ON ai.material_item_id = i.item_id
        WHERE i.item_type = 'MATERIAL'
          AND i.is_active = 1
        GROUP BY
            i.item_id,
            i.item_code,
            i.item_name
        ORDER BY
            available_qty ASC,
            i.item_code ASC
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

