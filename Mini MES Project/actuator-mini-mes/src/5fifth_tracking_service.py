from __future__ import annotations
from src.db import get_connection

def get_serial_summary(serial_no: str) -> dict:
    """Serial의 제품, 작업지시, 상태와 공정 진행률 조회"""

    serial_no = serial_no.strip()

    if not serial_no:
        raise ValueError('Serial 번호를 입력해야 합니다.')

    with get_connection() as connection:
        summary = connection.execute(
            """
            SELECT
                ps.product_serial_id,
                ps.serial_no,
                ps.status AS serial_status,
                wo.work_order_id,
                wo.work_order_no,
                wo.product_item_id,
                i.item_code AS product_code,
                i.item_name AS product_name,
                COUNT(rs.routing_step_id) AS total_process_count,
                COUNT(ph.process_history_id) AS completed_process_count,
                SUM(
                    CASE
                        WHEN ph.result = 'PASS' THEN 1
                        ELSE 0
                    END
                ) AS passed_process_count
            FROM product_serial AS ps
            JOIN work_order AS wo
                ON wo.work_order_id = ps.work_order_id
            JOIN item AS i
                ON i.item_id = wo.product_item_id
            JOIN routing_step AS rs
                ON rs.product_item_id = wo.product_item_id
               AND rs.is_active = 1
            LEFT JOIN process_history AS ph
                ON ph.product_serial_id = ps.product_serial_id
               AND ph.routing_step_id = rs.routing_step_id
            WHERE ps.serial_no = ?
            GROUP BY
                ps.product_serial_id,
                ps.serial_no,
                ps.status,
                wo.work_order_id,
                wo.work_order_no,
                wo.product_item_id,
                i.item_code,
                i.item_name
            """,
            (serial_no,),
        ).fetchone()

        if summary is None:
            raise ValueError(
                f"Serial 번호를 찾을 수 없습니다 : {serial_no}"
            )

        total_process_count = summary["total_process_count"]
        completed_process_count = summary["completed_process_count"]

        if total_process_count == 0:
            progress_rate = 0.0
        else:
            progress_rate = round(
                completed_process_count / total_process_count * 100,
                1,
            )

        current_process = connection.execute(
            """
            SELECT
                p.process_code,
                p.process_name,
                rs.sequence_no
            FROM routing_step AS rs
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE rs.product_item_id = ?
              AND rs.is_active = 1
              AND NOT EXISTS (
                  SELECT 1
                  FROM process_history AS ph
                  WHERE ph.product_serial_id = ?
                    AND ph.routing_step_id = rs.routing_step_id
              )
            ORDER BY rs.sequence_no
            LIMIT 1
            """,
            (
                summary["product_item_id"],
                summary["product_serial_id"],
            ),
        ).fetchone()

        result = dict(summary)
        result["progress_rate"] = progress_rate

        if summary["serial_status"] == "FAIL" or current_process is None:
            result["current_process_code"] = None
            result["current_process_name"] = None
            result["current_sequence_no"] = None
        else:
            result["current_process_code"] = current_process["process_code"]
            result["current_process_name"] = current_process["process_name"]
            result["current_sequence_no"] = current_process["sequence_no"]

        return result


def get_serial_process_status(serial_no: str) -> list[dict]:
    """Serial에 적용되는 전체 공정과 공정별 진행 상태를 조회한다."""

    serial_no = serial_no.strip()

    if not serial_no:
        raise ValueError("Serial 번호를 입력해야 합니다.")

    with get_connection() as connection:
        serial = connection.execute(
            """
            SELECT
                ps.product_serial_id,
                ps.status AS serial_status,
                wo.product_item_id
            FROM product_serial AS ps
            JOIN work_order AS wo
                ON wo.work_order_id = ps.work_order_id
            WHERE ps.serial_no = ?
            """,
            (serial_no,),
        ).fetchone()

        if serial is None:
            raise ValueError(
                f"Serial 번호를 찾을 수 없습니다 : {serial_no}"
            )

        process_rows = connection.execute(
            """
            SELECT
                rs.routing_step_id,
                rs.sequence_no,
                rs.is_required,
                p.process_code,
                p.process_name,
                p.process_type,
                ph.process_history_id,
                ph.result,
                ph.started_at,
                ph.completed_at,
                ph.remark
            FROM routing_step AS rs
            JOIN process AS p
                ON p.process_id = rs.process_id
            LEFT JOIN process_history AS ph
                ON ph.routing_step_id = rs.routing_step_id
               AND ph.product_serial_id = ?
            WHERE rs.product_item_id = ?
              AND rs.is_active = 1
            ORDER BY rs.sequence_no
            """,
            (
                serial["product_serial_id"],
                serial["product_item_id"],
            ),
        ).fetchall()

        results = []
        failure_occurred = False
        current_assigned = False

        for row in process_rows:
            process = dict(row)

            if process["result"] == "PASS":
                process["display_status"] = "COMPLETED"

            elif process["result"] == "FAIL":
                process["display_status"] = "FAILED"
                failure_occurred = True

            elif failure_occurred:
                process["display_status"] = "BLOCKED"

            elif not current_assigned:
                process["display_status"] = "CURRENT"
                current_assigned = True

            else:
                process["display_status"] = "WAITING"

            results.append(process)

        return results
