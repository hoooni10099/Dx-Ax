"""
학습 과정에서 사용한 단계별 작업지시·Serial 생성 함수.

현재 실제 기능에서는 사용하지 않으며,
src.services.create_work_order_with_serials()로 통합되었다.
"""

# # 작업지시 1건만 저장하는 함수, Serial은 x
# def create_work_order_only(
#     work_order_no: str,
#     product_item_code: str,
#     planned_qty: int,
#     due_date: str,
# ) -> int: # 정수를 반환

#     #각종 검사
#     work_order_no = work_order_no.strip()
#     # 입력값이 올바른지 확인
#     if not work_order_no:
#         raise ValueError('작업 지시 번호를 입력해야 합니다.')

#     if not isinstance(planned_qty, int) or isinstance(planned_qty, bool):
#         raise ValueError('계획 수량은 정수여야 합니다.')

#     if planned_qty <= 0:
#         raise ValueError('계획 수량은 1 이상이어야 합니다.')

#     try:
#         datetime.strptime(due_date, '%Y-%m-%d')
#     except ValueError as error:
#         raise ValueError(
#             '납기일은 YYYY-MM-DD 형식이어야 합니다.'
#         ) from error

#     # 생산 가능한 완제품인지 확인
#     product = find_active_product(product_item_code)

#     # 같은 작업 지시 번호가 이미 있는지 확인
#     with get_connection() as connection:
#         duplicated_order = connection.execute(
#             """
#             SELECT  work_order_id
#             FROM work_order
#             WHERE work_order_no = ?
#             """,
#             (work_order_no,),
#         ).fetchone()

#         if duplicated_order is not None:
#             raise ValueError(
#                 f'이미 등록된 작업 지시 번호입니다 : {work_order_no}'
#             )

#         # work_order Table에 한 행 삽입
#         cursor = connection.execute(
#             """
#             INSERT INTO work_order (
#                 work_order_no,
#                 product_item_id,
#                 planned_qty,
#                 due_date
#             )
#             VALUES (?, ?, ?, ?)
#             """,
#             (
#                 work_order_no,
#                 product["item_id"],
#                 planned_qty,
#                 due_date,
#             ),
#         )
#         # 새로 생성된 work_order_id 반환
#         work_order_id = cursor.lastrowid

#     return work_order_id

# # 작업 지시 수량만큼 Serial 생성
# def create_product_serials(work_order_id: int) -> list[str]:
#     with get_connection() as connection:
#         work_order = connection.execute(
#             """
#             SELECT
#                 work_order_no,
#                 planned_qty,
#                 status
#             FROM work_order
#             WHERE work_order_id = ?
#             """,
#             (work_order_id,),
#         ).fetchone()

#         # 전달 받은 work_order_id로 작업 지시를 찾음
#         if work_order is None:
#             raise ValueError(
#                 f'작업 지시를 찾을 수 없습니다 : {work_order_id}'
#             )
#         # 해당 작업 지시에 연결된 Serial이 몇 개인지 계산
#         existing_serial_count = connection.execute(
#             """
#             SELECT COUNT(*) AS serial_count
#             FROM product_serial
#             WHERE work_order_id = ?
#             """,
#             (work_order_id,),
#         ).fetchone()["serial_count"]

#         # 이미 Serial이 만들어졌는지 검사함
#         if existing_serial_count > 0:
#             raise ValueError(
#                 f'이미 serial이 생성된 작업 지시입니다 : {work_order_id}'
#             )

#         created_serial_numbers = [] # 앞으로 생성할 Serial 번호를 넣을 리스트

#         # 계획 수량만큼 Serial을 생성함
#         for sequence in range(1, work_order["planned_qty"] + 1):
#             serial_no = (
#                 f'{work_order['work_order_no']}-S{sequence:03d}'
#             )

#             connection.execute(
#                 """
#                 INSERT INTO product_serial (
#                     serial_no,
#                     work_order_id
#                 )
#                 VALUES (?, ?)
#                 """,
#                 (serial_no, work_order_id),
#             )

#             # 생성된 Serial 번호들을 리스트로 반환함
#             created_serial_numbers.append(serial_no)

#     return created_serial_numbers

