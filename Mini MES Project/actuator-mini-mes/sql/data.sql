-- 업데이트 미적용

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
------------------------------------


-- bom TABLE
-- ACT-Basic BOM
INSERT INTO bom (
    product_item_id,
    material_item_id,
    input_routing_step_id,
    required_qty,
    created_at
)
VALUES
    (
        (SELECT item_id
         FROM item
         WHERE item_code = 'ACT-BASIC'),

        (SELECT item_id
         FROM item
         WHERE item_code = 'MAT-MOTOR'),

        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS i
                ON i.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE i.item_code = 'ACT-BASIC'
              AND p.process_code = 'PROC-MOTOR'
        ),

        1,
        CURRENT_TIMESTAMP
    ),
    (
        (SELECT item_id
         FROM item
         WHERE item_code = 'ACT-BASIC'),

        (SELECT item_id
         FROM item
         WHERE item_code = 'MAT-HOUSING'),

        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS i
                ON i.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE i.item_code = 'ACT-BASIC'
              AND p.process_code = 'PROC-MOTOR'
        ),

        1,
        CURRENT_TIMESTAMP
    ),
    (
        (SELECT item_id
         FROM item
         WHERE item_code = 'ACT-BASIC'),

        (SELECT item_id
         FROM item
         WHERE item_code = 'MAT-GEAR'),

        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS i
                ON i.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE i.item_code = 'ACT-BASIC'
              AND p.process_code = 'PROC-GEAR'
        ),

        1,
        CURRENT_TIMESTAMP
    ),
    (
        (SELECT item_id
         FROM item
         WHERE item_code = 'ACT-BASIC'),

        (SELECT item_id
         FROM item
         WHERE item_code = 'MAT-PCB'),

        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS i
                ON i.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE i.item_code = 'ACT-BASIC'
              AND p.process_code = 'PROC-PCB'
        ),

        1,
        CURRENT_TIMESTAMP
    );

-- ACT-Sensor BOM
INSERT INTO bom (
    product_item_id,
    material_item_id,
    input_routing_step_id,
    required_qty,
    created_at
)
VALUES
    (
        (SELECT item_id
         FROM item
         WHERE item_code = 'ACT-SENSOR'),

        (SELECT item_id
         FROM item
         WHERE item_code = 'MAT-MOTOR'),

        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS i
                ON i.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE i.item_code = 'ACT-SENSOR'
              AND p.process_code = 'PROC-MOTOR'
        ),

        1,
        CURRENT_TIMESTAMP
    ),
    (
        (SELECT item_id
         FROM item
         WHERE item_code = 'ACT-SENSOR'),

        (SELECT item_id
         FROM item
         WHERE item_code = 'MAT-HOUSING'),

        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS i
                ON i.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE i.item_code = 'ACT-SENSOR'
              AND p.process_code = 'PROC-MOTOR'
        ),

        1,
        CURRENT_TIMESTAMP
    ),
    (
        (SELECT item_id
         FROM item
         WHERE item_code = 'ACT-SENSOR'),

        (SELECT item_id
         FROM item
         WHERE item_code = 'MAT-GEAR'),

        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS i
                ON i.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE i.item_code = 'ACT-SENSOR'
              AND p.process_code = 'PROC-GEAR'
        ),

        1,
        CURRENT_TIMESTAMP
    ),
    (
        (SELECT item_id
         FROM item
         WHERE item_code = 'ACT-SENSOR'),

        (SELECT item_id
         FROM item
         WHERE item_code = 'MAT-SENSOR'),

        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS i
                ON i.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE i.item_code = 'ACT-SENSOR'
              AND p.process_code = 'PROC-SENSOR'
        ),

        1,
        CURRENT_TIMESTAMP
    ),
    (
        (SELECT item_id
         FROM item
         WHERE item_code = 'ACT-SENSOR'),

        (SELECT item_id
         FROM item
         WHERE item_code = 'MAT-PCB'),

        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS i
                ON i.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE i.item_code = 'ACT-SENSOR'
              AND p.process_code = 'PROC-PCB'
        ),

        1,
        CURRENT_TIMESTAMP
    );



SELECT
    b.bom_id,
    product.item_code AS product_code,
    product.item_name AS product_name,
    material.item_code AS material_code,
    material.item_name AS material_name,
    b.required_qty,
    rs.sequence_no AS input_sequence,
    p.process_code AS input_process_code,
    p.process_name AS input_process_name,
    b.is_active,
    b.created_at
FROM bom AS b
JOIN item AS product
    ON product.item_id = b.product_item_id
JOIN item AS material
    ON material.item_id = b.material_item_id
JOIN routing_step AS rs
    ON rs.routing_step_id = b.input_routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
ORDER BY
    product.item_code,
    rs.sequence_no,
    material.item_code;
