
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


-------------------------------------------


-- material_lot Table
INSERT INTO material_lot (
    lot_no,
    material_item_id,
    received_qty,
    received_date
)
VALUES
    (
        'LOT-MOTOR-20260701-A',
        (SELECT item_id FROM item WHERE item_code = 'MAT-MOTOR'),
        50,
        '2026-07-01'
    ),
    (
        'LOT-MOTOR-20260715-B',
        (SELECT item_id FROM item WHERE item_code = 'MAT-MOTOR'),
        50,
        '2026-07-15'
    ),
    (
        'LOT-GEAR-20260701-A',
        (SELECT item_id FROM item WHERE item_code = 'MAT-GEAR'),
        50,
        '2026-07-01'
    ),
    (
        'LOT-GEAR-20260715-B',
        (SELECT item_id FROM item WHERE item_code = 'MAT-GEAR'),
        50,
        '2026-07-15'
    ),
    (
        'LOT-HOUSING-20260701-A',
        (SELECT item_id FROM item WHERE item_code = 'MAT-HOUSING'),
        50,
        '2026-07-01'
    ),
    (
        'LOT-HOUSING-20260715-B',
        (SELECT item_id FROM item WHERE item_code = 'MAT-HOUSING'),
        50,
        '2026-07-15'
    ),
    (
        'LOT-PCB-20260701-A',
        (SELECT item_id FROM item WHERE item_code = 'MAT-PCB'),
        50,
        '2026-07-01'
    ),
    (
        'LOT-PCB-20260715-B',
        (SELECT item_id FROM item WHERE item_code = 'MAT-PCB'),
        50,
        '2026-07-15'
    ),
    (
        'LOT-SENSOR-20260701-A',
        (SELECT item_id FROM item WHERE item_code = 'MAT-SENSOR'),
        30,
        '2026-07-01'
    ),
    (
        'LOT-SENSOR-20260715-B',
        (SELECT item_id FROM item WHERE item_code = 'MAT-SENSOR'),
        30,
        '2026-07-15'
    );


SELECT
    ml.material_lot_id,
    ml.lot_no,
    i.item_code,
    i.item_name,
    ml.received_qty,
    ml.received_date,
    ml.status,
    ml.created_at
FROM material_lot AS ml
JOIN item AS i
    ON i.item_id = ml.material_item_id
ORDER BY
    i.item_code,
    ml.received_date,
    ml.material_lot_id;


----------------------------------------------------------------------


-- work_order Table
INSERT INTO work_order (
    work_order_no,
    product_item_id,
    planned_qty,
    due_date
)
VALUES
    (
        'WO-20260728-001',
        (
            SELECT item_id
            FROM item
            WHERE item_code = 'ACT-BASIC'
        ),
        10,
        '2026-08-05'
    ),
    (
        'WO-20260728-002',
        (
            SELECT item_id
            FROM item
            WHERE item_code = 'ACT-SENSOR'
        ),
        10,
        '2026-08-07'
    );

SELECT
    wo.work_order_id,
    wo.work_order_no,
    i.item_code AS product_code,
    i.item_name AS product_name,
    wo.planned_qty,
    wo.status,
    wo.due_date,
    wo.started_at,
    wo.completed_at,
    wo.created_at
FROM work_order AS wo
JOIN item AS i
    ON i.item_id = wo.product_item_id
ORDER BY wo.work_order_id;


UPDATE work_order
SET
    status = 'IN_PROGRESS',
    started_at = CURRENT_TIMESTAMP
WHERE work_order_no = 'WO-20260728-001'
  AND status = 'PLANNED';

UPDATE work_order
SET
    status = 'COMPLETED',
    completed_at = CURRENT_TIMESTAMP
WHERE work_order_no = 'WO-20260728-001'
  AND status = 'IN_PROGRESS';

----------------------------------------------

--product_serial Table
-- 기본형 제품 10개
INSERT INTO product_serial (
    serial_no,
    work_order_id
)
VALUES
    (
        'BASIC-20260728-001',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    ),
    (
        'BASIC-20260728-002',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    ),
    (
        'BASIC-20260728-003',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    ),
    (
        'BASIC-20260728-004',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    ),
    (
        'BASIC-20260728-005',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    ),
    (
        'BASIC-20260728-006',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    ),
    (
        'BASIC-20260728-007',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    ),
    (
        'BASIC-20260728-008',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    ),
    (
        'BASIC-20260728-009',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    ),
    (
        'BASIC-20260728-010',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-001')
    );


-- 센서형 제품 10개
INSERT INTO product_serial (
    serial_no,
    work_order_id
)
VALUES
    (
        'SENSOR-20260728-001',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    ),
    (
        'SENSOR-20260728-002',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    ),
    (
        'SENSOR-20260728-003',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    ),
    (
        'SENSOR-20260728-004',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    ),
    (
        'SENSOR-20260728-005',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    ),
    (
        'SENSOR-20260728-006',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    ),
    (
        'SENSOR-20260728-007',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    ),
    (
        'SENSOR-20260728-008',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    ),
    (
        'SENSOR-20260728-009',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    ),
    (
        'SENSOR-20260728-010',
        (SELECT work_order_id
         FROM work_order
         WHERE work_order_no = 'WO-20260728-002')
    );


SELECT
    ps.product_serial_id,
    ps.serial_no,
    wo.work_order_no,
    i.item_code AS product_code,
    i.item_name AS product_name,
    ps.status,
    ps.started_at,
    ps.completed_at,
    ps.created_at
FROM product_serial AS ps
JOIN work_order AS wo
    ON wo.work_order_id = ps.work_order_id
JOIN item AS i
    ON i.item_id = wo.product_item_id
ORDER BY
    wo.work_order_no,
    ps.serial_no;


SELECT
    wo.work_order_no,
    wo.planned_qty,
    COUNT(ps.product_serial_id) AS serial_count,
    wo.planned_qty - COUNT(ps.product_serial_id) AS difference
FROM work_order AS wo
LEFT JOIN product_serial AS ps
    ON ps.work_order_id = wo.work_order_id
GROUP BY
    wo.work_order_id,
    wo.work_order_no,
    wo.planned_qty
ORDER BY wo.work_order_no;


