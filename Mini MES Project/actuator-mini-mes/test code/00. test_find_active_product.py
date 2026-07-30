from src.first_work_order_service import find_active_product


product = find_active_product("ACT-BASIC")

print("품목 ID:", product["item_id"])
print("품목 코드:", product["item_code"])
print("품목명:", product["item_name"])
