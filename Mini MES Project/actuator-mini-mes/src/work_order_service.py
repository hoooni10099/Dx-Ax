from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from datetime import date
import sqlite3
from src.db import get_connection

@dataclass(frozen=True)
class ServiceResult:
    success: bool
    message: str

def get_active_products() -> pd.DataFrame:
    """작업지시를 생성할 수 있는 활성 완제품을 조회한다."""

    sql = """
        SELECT
            item_id,
            item_code,
            item_name
        FROM item
        WHERE item_type = 'PRODUCT'
          AND is_active = 1
        ORDER BY item_code
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)


def get_work_orders(
    product_item_id: int | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> pd.DataFrame:
    """등록된 작업지시를 조건에 따라 조회한다."""

    keyword = (keyword or "").strip()

    sql = """
        SELECT
            wo.work_order_no AS 작업지시번호,
            i.item_code AS 제품코드,
            i.item_name AS 제품명,
            wo.planned_qty AS 계획수량,
            COUNT(ps.product_serial_id) AS Serial발급수량,
            CASE wo.status
                WHEN 'PLANNED' THEN '계획'
                WHEN 'IN_PROGRESS' THEN '생산 중'
                WHEN 'COMPLETED' THEN '완료'
                WHEN 'CANCELLED' THEN '취소'
                ELSE wo.status
            END AS 상태,
            wo.due_date AS 납기일,
            wo.started_at AS 시작일시,
            wo.completed_at AS 완료일시,
            wo.created_at AS 등록일시
        FROM work_order AS wo
        JOIN item AS i
          ON i.item_id = wo.product_item_id
        LEFT JOIN product_serial AS ps
          ON ps.work_order_id = wo.work_order_id
        WHERE 1 = 1
    """

    params: list[object] = []

    if product_item_id is not None:
        sql += """
            AND wo.product_item_id = ?
        """
        params.append(product_item_id)

    if status is not None:
        sql += """
            AND wo.status = ?
        """
        params.append(status)

    if keyword:
        sql += """
            AND (
                wo.work_order_no LIKE ?
                OR i.item_code LIKE ?
                OR i.item_name LIKE ?
            )
        """

        search_keyword = f"%{keyword}%"
        params.extend(
            [
                search_keyword,
                search_keyword,
                search_keyword,
            ]
        )

    sql += """
        GROUP BY
            wo.work_order_id,
            wo.work_order_no,
            i.item_code,
            i.item_name,
            wo.planned_qty,
            wo.status,
            wo.due_date,
            wo.started_at,
            wo.completed_at,
            wo.created_at
        ORDER BY wo.created_at DESC, wo.work_order_id DESC
    """

    with get_connection() as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )

def create_work_order(
    work_order_no: str,
    product_item_id: int,
    planned_qty: int,
    due_date: str,
) -> ServiceResult:
    """신규 작업지시를 검증한 후 등록한다."""

    work_order_no = (work_order_no or "").strip().upper()
    due_date = (due_date or "").strip()

    if not work_order_no:
        return ServiceResult(
            success=False,
            message="작업지시 번호를 입력해주세요.",
        )

    try:
        planned_qty = int(planned_qty)
    except (TypeError, ValueError):
        return ServiceResult(
            success=False,
            message="계획 수량은 정수로 입력해주세요.",
        )

    if planned_qty < 1:
        return ServiceResult(
            success=False,
            message="계획 수량은 1개 이상이어야 합니다.",
        )

    try:
        parsed_due_date = date.fromisoformat(due_date)
    except (TypeError, ValueError):
        return ServiceResult(
            success=False,
            message="납기일은 YYYY-MM-DD 형식이어야 합니다.",
        )

    if parsed_due_date < date.today():
        return ServiceResult(
            success=False,
            message="납기일은 오늘보다 이전일 수 없습니다.",
        )

    with get_connection() as connection:
        product = connection.execute(
            """
            SELECT
                item_code,
                item_name
            FROM item
            WHERE item_id = ?
              AND item_type = 'PRODUCT'
              AND is_active = 1
            """,
            (product_item_id,),
        ).fetchone()

        if product is None:
            return ServiceResult(
                success=False,
                message="선택한 완제품이 존재하지 않거나 비활성 상태입니다.",
            )

        duplicate = connection.execute(
            """
            SELECT 1
            FROM work_order
            WHERE work_order_no = ?
            """,
            (work_order_no,),
        ).fetchone()

        if duplicate is not None:
            return ServiceResult(
                success=False,
                message=f"이미 등록된 작업지시 번호입니다: {work_order_no}",
            )

        try:
            connection.execute(
                """
                INSERT INTO work_order (
                    work_order_no,
                    product_item_id,
                    planned_qty,
                    status,
                    due_date
                )
                VALUES (?, ?, ?, 'PLANNED', ?)
                """,
                (
                    work_order_no,
                    product_item_id,
                    planned_qty,
                    due_date,
                ),
            )
            connection.commit()

        except sqlite3.IntegrityError:
            return ServiceResult(
                success=False,
                message="작업지시 등록 중 데이터 제약조건 오류가 발생했습니다.",
            )

    return ServiceResult(
        success=True,
        message=(
            f"{work_order_no} 작업지시가 등록되었습니다. "
            f"제품: {product['item_code']} - {product['item_name']}, "
            f"계획 수량: {planned_qty}개"
        ),
    )

