from src.services import create_product_serials


try:
    serial_numbers = create_product_serials(work_order_id=1)

    print("생성된 Serial 번호:")

    for serial_no in serial_numbers:
        print(serial_no)

except ValueError as error:
    print("Serial 생성 실패:", error)
