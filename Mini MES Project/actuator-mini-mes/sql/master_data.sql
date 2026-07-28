
-- item TABLE
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

-- process TABLE
INSERT INTO process (
    process_code,
    process_name,
    process_type
)
VALUES
    ('PROC-MOTOR',    '모터 조립',       'ASSEMBLY'),
    ('PROC-GEAR',     '기어 조립',       'ASSEMBLY'),
    ('PROC-SENSOR',   '위치센서 조립',   'ASSEMBLY'),
    ('PROC-PCB',      'PCB 조립',        'ASSEMBLY'),
    ('PROC-VISUAL',   '외관 확인',       'INSPECTION'),
    ('PROC-EOL',      'EOL 성능 검사',   'INSPECTION'),
    ('PROC-COMPLETE', '생산 완료',       'COMPLETION');
-----------------------------------------------------------

-- routing_step TABLE
-- ACT-BASIC Routing
INSERT INTO routing_step (
    product_item_id,
    process_id,
    sequence_no
)
VALUES
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-BASIC'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-MOTOR'),
        10
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-BASIC'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-GEAR'),
        20
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-BASIC'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-PCB'),
        30
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-BASIC'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-VISUAL'),
        40
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-BASIC'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-EOL'),
        50
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-BASIC'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-COMPLETE'),
        60
    );

-- ACT-SENSOR Routing
INSERT INTO routing_step (
    product_item_id,
    process_id,
    sequence_no
)
VALUES
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-SENSOR'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-MOTOR'),
        10
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-SENSOR'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-GEAR'),
        20
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-SENSOR'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-SENSOR'),
        30
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-SENSOR'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-PCB'),
        40
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-SENSOR'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-VISUAL'),
        50
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-SENSOR'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-EOL'),
        60
    ),
    (
        (SELECT item_id FROM item WHERE item_code = 'ACT-SENSOR'),
        (SELECT process_id FROM process WHERE process_code = 'PROC-COMPLETE'),
        70
    );



SELECT
    rs.routing_step_id,
    i.item_code,
    i.item_name,
    rs.sequence_no,
    p.process_code,
    p.process_name,
    p.process_type,
    rs.is_required,
    rs.is_active
FROM routing_step AS rs
JOIN item AS i
    ON i.item_id = rs.product_item_id
JOIN process AS p
    ON p.process_id = rs.process_id
ORDER BY
    i.item_code,
    rs.sequence_no;


SELECT
    i.item_code,
    COUNT(*) AS routing_step_count
FROM routing_step AS rs
JOIN item AS i
    ON i.item_id = rs.product_item_id
GROUP BY i.item_code
ORDER BY i.item_code;




