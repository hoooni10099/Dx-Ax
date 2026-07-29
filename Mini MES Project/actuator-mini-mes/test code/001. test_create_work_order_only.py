from src.services import create_work_order_only


work_order_id = create_work_order_only(
    work_order_no="WO-20260729-001",
    product_item_code="ACT-BASIC",
    planned_qty=3,
    due_date="2026-08-05",
)

print("생성된 작업지시 ID:", work_order_id)




-------------------------------------------------------
SQL

SELECT
    wo.work_order_id,
    wo.work_order_no,
    i.item_code,
    i.item_name,
    wo.planned_qty,
    wo.status,
    wo.due_date,
    wo.created_at
FROM work_order AS wo
JOIN item AS i
    ON i.item_id = wo.product_item_id;
