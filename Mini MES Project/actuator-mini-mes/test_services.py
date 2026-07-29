from src.services import find_active_product
from src.services import create_work_order_only


product = find_active_product("ACT-BASIC")

try:
    product = find_active_product("NOT-EXISTS")
    print("품목 ID:", product["item_id"])
    print("품목 코드:", product["item_code"])
    print("품목명:", product["item_name"])

except ValueError as error:
    print("조회 실패:", error)

work_order_id = create_work_order_only(
    work_order_no="WO-20260729-001",
    product_item_code="ACT-BASIC",
    planned_qty=3,
    due_date="2026-08-05",
)

print("생성된 작업지시 ID:", work_order_id)
