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

def get_serial_issuable_work_orders() -> pd.DataFrame:
    """Serial Number를 추가 발급할 수 있는 작업지시를 조회한다."""

    sql = """
        SELECT
            wo.work_order_id,
            wo.work_order_no,
            wo.product_item_id,
            i.item_code,
            i.item_name,
            wo.planned_qty,
            COUNT(ps.product_serial_id) AS issued_qty,
            wo.planned_qty - COUNT(ps.product_serial_id) AS remaining_qty
        FROM work_order AS wo
        JOIN item AS i
          ON i.item_id = wo.product_item_id
        LEFT JOIN product_serial AS ps
          ON ps.work_order_id = wo.work_order_id
        WHERE wo.status IN ('PLANNED', 'IN_PROGRESS')
        GROUP BY
            wo.work_order_id,
            wo.work_order_no,
            wo.product_item_id,
            i.item_code,
            i.item_name,
            wo.planned_qty
        HAVING COUNT(ps.product_serial_id) < wo.planned_qty
        ORDER BY wo.created_at, wo.work_order_id
    """

    with get_connection() as connection:
        return pd.read_sql_query(sql, connection)

def issue_product_serials(
    work_order_id: int,
    issue_qty: int,
) -> ServiceResult:
    """작업지시의 잔여수량 범위에서 제품 Serial을 일괄 발급한다."""

    try:
        work_order_id = int(work_order_id)
        issue_qty = int(issue_qty)
    except (TypeError, ValueError):
        return ServiceResult(
            success=False,
            message="작업지시와 발급수량을 올바르게 입력해주세요.",
        )

    if issue_qty < 1:
        return ServiceResult(
            success=False,
            message="Serial 발급수량은 1개 이상이어야 합니다.",
        )

    issue_date = date.today().strftime("%Y%m%d")

    with get_connection() as connection:
        try:
            # 동시에 여러 사용자가 발급하는 경우 중복 계산을 방지한다.
            connection.execute("BEGIN IMMEDIATE")

            work_order = connection.execute(
                """
                SELECT
                    wo.work_order_no,
                    wo.planned_qty,
                    wo.status,
                    i.item_code,
                    i.item_name,
                    COUNT(ps.product_serial_id) AS issued_qty
                FROM work_order AS wo
                JOIN item AS i
                  ON i.item_id = wo.product_item_id
                LEFT JOIN product_serial AS ps
                  ON ps.work_order_id = wo.work_order_id
                WHERE wo.work_order_id = ?
                GROUP BY
                    wo.work_order_id,
                    wo.work_order_no,
                    wo.planned_qty,
                    wo.status,
                    i.item_code,
                    i.item_name
                """,
                (work_order_id,),
            ).fetchone()

            if work_order is None:
                connection.rollback()
                return ServiceResult(
                    success=False,
                    message="선택한 작업지시를 찾을 수 없습니다.",
                )

            if work_order["status"] not in ("PLANNED", "IN_PROGRESS"):
                connection.rollback()
                return ServiceResult(
                    success=False,
                    message="계획 또는 생산 중인 작업지시에서만 Serial을 발급할 수 있습니다.",
                )

            remaining_qty = (
                work_order["planned_qty"] - work_order["issued_qty"]
            )

            if remaining_qty < 1:
                connection.rollback()
                return ServiceResult(
                    success=False,
                    message="이 작업지시는 계획수량만큼 Serial이 모두 발급되었습니다.",
                )

            if issue_qty > remaining_qty:
                connection.rollback()
                return ServiceResult(
                    success=False,
                    message=(
                        f"발급 가능 수량을 초과했습니다. "
                        f"현재 발급 가능 수량: {remaining_qty}개"
                    ),
                )

            serial_prefix = (
                f"{work_order['item_code']}-{issue_date}-"
            )

            existing_serials = connection.execute(
                """
                SELECT serial_no
                FROM product_serial
                WHERE serial_no LIKE ?
                """,
                (f"{serial_prefix}%",),
            ).fetchall()

            sequence_numbers: list[int] = []

            for row in existing_serials:
                suffix = row["serial_no"].removeprefix(serial_prefix)

                if suffix.isdigit():
                    sequence_numbers.append(int(suffix))

            next_sequence = (
                max(sequence_numbers, default=0) + 1
            )

            issued_serials: list[str] = []

            for offset in range(issue_qty):
                serial_no = (
                    f"{serial_prefix}"
                    f"{next_sequence + offset:04d}"
                )

                connection.execute(
                    """
                    INSERT INTO product_serial (
                        serial_no,
                        work_order_id,
                        status
                    )
                    VALUES (?, ?, 'CREATED')
                    """,
                    (
                        serial_no,
                        work_order_id,
                    ),
                )

                issued_serials.append(serial_no)

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()
            return ServiceResult(
                success=False,
                message="Serial 발급 중 데이터 중복 또는 제약조건 오류가 발생했습니다.",
            )

        except sqlite3.OperationalError:
            connection.rollback()
            return ServiceResult(
                success=False,
                message="Serial 발급 중 데이터베이스 처리 오류가 발생했습니다.",
            )

    return ServiceResult(
        success=True,
        message=(
            f"{work_order['work_order_no']} 작업지시에 "
            f"Serial {issue_qty}개를 발급했습니다. "
            f"발급 범위: {issued_serials[0]} ~ {issued_serials[-1]}"
        ),
    )

def get_product_serials() -> pd.DataFrame:
    """발급된 제품 Serial과 작업지시 정보를 조회한다."""

    sql = """
        SELECT
            ps.product_serial_id,
            ps.serial_no,
            wo.work_order_no,
            i.item_code,
            i.item_name,
            ps.status,
            ps.started_at,
            ps.completed_at,
            ps.created_at
        FROM product_serial AS ps
        JOIN work_order AS wo
          ON wo.work_order_id = ps.work_order_id
        JOIN item AS i
          ON i.item_id = wo.product_item_id
        ORDER BY
            ps.created_at DESC,
            ps.product_serial_id DESC
    """

    status_labels = {
        "CREATED": "발급",
        "IN_PROGRESS": "생산 중",
        "PASS": "합격",
        "FAIL": "불합격",
    }

    with get_connection() as connection:
        serials = pd.read_sql_query(sql, connection)

    if serials.empty:
        return pd.DataFrame(
            columns=[
                "Serial Number",
                "작업지시번호",
                "제품코드",
                "제품명",
                "상태",
                "시작일시",
                "완료일시",
                "발급일시",
            ]
        )

    serials["status"] = (
        serials["status"]
        .map(status_labels)
        .fillna(serials["status"])
    )

    return serials.rename(
        columns={
            "serial_no": "Serial Number",
            "work_order_no": "작업지시번호",
            "item_code": "제품코드",
            "item_name": "제품명",
            "status": "상태",
            "started_at": "시작일시",
            "completed_at": "완료일시",
            "created_at": "발급일시",
        }
    ).drop(columns=["product_serial_id"])
