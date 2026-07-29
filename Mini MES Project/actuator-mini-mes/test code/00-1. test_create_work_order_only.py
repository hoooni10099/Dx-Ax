from src.services import create_work_order_only


work_order_id = create_work_order_only(
    work_order_no="WO-20260729-001",
    product_item_code="ACT-BASIC",
    planned_qty=3,
    due_date="2026-08-05",
)

print("생성된 작업지시 ID:", work_order_id)
