import inspect

from src.first_work_order_service import (
    create_work_order_with_serials,
    update_work_order_status,
)
from src.second_production_service import start_product_serial
from src.third_material_service import (
    register_material_consumption,
    register_process_result,
    get_material_lot_inventory,
)
from src.fourth_eol_service import (
    register_eol_test_result,
    complete_production,
)

functions = [
    create_work_order_with_serials,
    update_work_order_status,
    start_product_serial,
    register_material_consumption,
    register_process_result,
    get_material_lot_inventory,
    register_eol_test_result,
    complete_production,
]

for function in functions:
    print(f"{function.__name__}{inspect.signature(function)}")
