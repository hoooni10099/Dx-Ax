INSERT INTO item (
    item_code,
    item_name,
    item_type
)
VALUES
    ('ACT-BASIC',  '기본형 전동 액추에이터', 'PRODUCT'),
    ('ACT-SENSOR', '센서형 전동 액추에이터', 'PRODUCT'),
    ('MAT-MOTOR',  'DC 모터',                'MATERIAL'),
    ('MAT-GEAR',   '감속기',                 'MATERIAL'),
    ('MAT-HOUSING','하우징',                 'MATERIAL'),
    ('MAT-PCB',    'PCB',                    'MATERIAL'),
    ('MAT-SENSOR', '위치센서',               'MATERIAL');


# is_active 비활성화
UPDATE item
SET is_active = 0
WHERE item_code = 'MAT-SENSOR';
---------------------------------------------------------

