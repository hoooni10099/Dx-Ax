
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

--------------------------------------------------------


--모터 조립
INSERT INTO process_history (
    product_serial_id,
    routing_step_id
)
VALUES (
    (
        SELECT product_serial_id
        FROM product_serial
        WHERE serial_no = 'BASIC-20260728-001'
    ),
    (
        SELECT rs.routing_step_id
        FROM routing_step AS rs
        JOIN item AS i
            ON i.item_id = rs.product_item_id
        JOIN process AS p
            ON p.process_id = rs.process_id
        WHERE i.item_code = 'ACT-BASIC'
          AND p.process_code = 'PROC-MOTOR'
    )
);

-- 개별 제품과 작업지시도 생산 진행 상태로 변경
UPDATE product_serial
SET
    status = 'IN_PROGRESS',
    started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
WHERE serial_no = 'BASIC-20260728-001'
  AND status = 'CREATED';

UPDATE work_order
SET
    status = 'IN_PROGRESS',
    started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
WHERE work_order_id = (
    SELECT work_order_id
    FROM product_serial
    WHERE serial_no = 'BASIC-20260728-001'
)
AND status = 'PLANNED';

-- 공정 완료
UPDATE process_history
SET
    result = 'PASS',
    completed_at = CURRENT_TIMESTAMP,
    remark = '정상 조립 완료'
WHERE product_serial_id = (
    SELECT product_serial_id
    FROM product_serial
    WHERE serial_no = 'BASIC-20260728-001'
)
AND routing_step_id = (
    SELECT rs.routing_step_id
    FROM routing_step AS rs
    JOIN item AS i
        ON i.item_id = rs.product_item_id
    JOIN process AS p
        ON p.process_id = rs.process_id
    WHERE i.item_code = 'ACT-BASIC'
      AND p.process_code = 'PROC-MOTOR'
)
AND completed_at IS NULL;

--실패
UPDATE process_history
SET
    result = 'FAIL',
    completed_at = CURRENT_TIMESTAMP,
    remark = '모터 결선 불량'
WHERE process_history_id = ?;


SELECT
    ps.serial_no,
    i.item_code AS product_code,
    rs.sequence_no,
    p.process_code,
    p.process_name,
    ph.started_at,
    ph.completed_at,
    ph.result,
    ph.remark
FROM process_history AS ph
JOIN product_serial AS ps
    ON ps.product_serial_id = ph.product_serial_id
JOIN work_order AS wo
    ON wo.work_order_id = ps.work_order_id
JOIN item AS i
    ON i.item_id = wo.product_item_id
JOIN routing_step AS rs
    ON rs.routing_step_id = ph.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
ORDER BY
    ps.serial_no,
    rs.sequence_no;


----------------------------------------------

--material_consumption Table

INSERT INTO material_consumption (
    product_serial_id,
    material_lot_id,
    routing_step_id,
    consumed_qty
)
VALUES
    (
        (
            SELECT product_serial_id
            FROM product_serial
            WHERE serial_no = 'BASIC-20260728-001'
        ),
        (
            SELECT material_lot_id
            FROM material_lot
            WHERE lot_no = 'LOT-MOTOR-20260701-A'
        ),
        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS product
                ON product.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE product.item_code = 'ACT-BASIC'
              AND p.process_code = 'PROC-MOTOR'
        ),
        1
    ),
    (
        (
            SELECT product_serial_id
            FROM product_serial
            WHERE serial_no = 'BASIC-20260728-001'
        ),
        (
            SELECT material_lot_id
            FROM material_lot
            WHERE lot_no = 'LOT-HOUSING-20260701-A'
        ),
        (
            SELECT rs.routing_step_id
            FROM routing_step AS rs
            JOIN item AS product
                ON product.item_id = rs.product_item_id
            JOIN process AS p
                ON p.process_id = rs.process_id
            WHERE product.item_code = 'ACT-BASIC'
              AND p.process_code = 'PROC-MOTOR'
        ),
        1
    );


SELECT
    mc.consumption_id,
    ps.serial_no,
    product.item_code AS product_code,
    material.item_code AS material_code,
    material.item_name AS material_name,
    ml.lot_no,
    mc.consumed_qty,
    rs.sequence_no,
    p.process_code,
    p.process_name,
    mc.consumed_at
FROM material_consumption AS mc
JOIN product_serial AS ps
    ON ps.product_serial_id = mc.product_serial_id
JOIN work_order AS wo
    ON wo.work_order_id = ps.work_order_id
JOIN item AS product
    ON product.item_id = wo.product_item_id
JOIN material_lot AS ml
    ON ml.material_lot_id = mc.material_lot_id
JOIN item AS material
    ON material.item_id = ml.material_item_id
JOIN routing_step AS rs
    ON rs.routing_step_id = mc.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
ORDER BY
    ps.serial_no,
    rs.sequence_no,
    material.item_code;


SELECT
    ml.material_lot_id,
    ml.lot_no,
    i.item_code,
    i.item_name,
    ml.received_qty,
    COALESCE(SUM(mc.consumed_qty), 0) AS consumed_qty,
    ml.received_qty
        - COALESCE(SUM(mc.consumed_qty), 0) AS remaining_qty,
    ml.status
FROM material_lot AS ml
JOIN item AS i
    ON i.item_id = ml.material_item_id
LEFT JOIN material_consumption AS mc
    ON mc.material_lot_id = ml.material_lot_id
GROUP BY
    ml.material_lot_id,
    ml.lot_no,
    i.item_code,
    i.item_name,
    ml.received_qty,
    ml.status
ORDER BY
    i.item_code,
    ml.received_date,
    ml.material_lot_id;

SELECT
    ps.serial_no,
    material.item_code,
    material.item_name,
    ml.lot_no,
    mc.consumed_qty,
    p.process_name,
    mc.consumed_at
FROM material_consumption AS mc
JOIN product_serial AS ps
    ON ps.product_serial_id = mc.product_serial_id
JOIN material_lot AS ml
    ON ml.material_lot_id = mc.material_lot_id
JOIN item AS material
    ON material.item_id = ml.material_item_id
JOIN routing_step AS rs
    ON rs.routing_step_id = mc.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
WHERE ps.serial_no = 'BASIC-20260728-001'
ORDER BY
    rs.sequence_no,
    material.item_code;


SELECT
    ml.lot_no,
    material.item_code AS material_code,
    ps.serial_no,
    product.item_code AS product_code,
    wo.work_order_no,
    p.process_name,
    mc.consumed_qty,
    mc.consumed_at,
    ps.status AS product_status
FROM material_consumption AS mc
JOIN material_lot AS ml
    ON ml.material_lot_id = mc.material_lot_id
JOIN item AS material
    ON material.item_id = ml.material_item_id
JOIN product_serial AS ps
    ON ps.product_serial_id = mc.product_serial_id
JOIN work_order AS wo
    ON wo.work_order_id = ps.work_order_id
JOIN item AS product
    ON product.item_id = wo.product_item_id
JOIN routing_step AS rs
    ON rs.routing_step_id = mc.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
WHERE ml.lot_no = 'LOT-MOTOR-20260701-A'
ORDER BY ps.serial_no;


--------------------------------------------
--eol_test_result Table


EOL 이전 공정 PASS 완료
→ EOL process_history 생성
→ EOL 검사 결과 저장
→ process_history 완료 처리
→ 제품 Serial PASS/FAIL 처리


SELECT
    ph.process_history_id,
    ps.serial_no,
    p.process_code,
    p.process_name,
    ph.started_at,
    ph.completed_at,
    ph.result
FROM process_history AS ph
JOIN product_serial AS ps
    ON ps.product_serial_id = ph.product_serial_id
JOIN routing_step AS rs
    ON rs.routing_step_id = ph.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
WHERE ps.serial_no = 'BASIC-20260728-001'
  AND p.process_code = 'PROC-EOL';


INSERT INTO process_history (
    product_serial_id,
    routing_step_id
)
SELECT
    ps.product_serial_id,
    rs.routing_step_id
FROM product_serial AS ps
JOIN work_order AS wo
    ON wo.work_order_id = ps.work_order_id
JOIN routing_step AS rs
    ON rs.product_item_id = wo.product_item_id
JOIN process AS p
    ON p.process_id = rs.process_id
WHERE ps.serial_no = 'BASIC-20260728-001'
  AND p.process_code = 'PROC-EOL';


SELECT
    ph.process_history_id,
    ps.serial_no,
    p.process_code
FROM process_history AS ph
JOIN product_serial AS ps
    ON ps.product_serial_id = ph.product_serial_id
JOIN routing_step AS rs
    ON rs.routing_step_id = ph.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
WHERE ps.serial_no = 'BASIC-20260728-001'
  AND p.process_code = 'PROC-EOL';


INSERT INTO eol_test_result (
    process_history_id,
    forward_ok,
    reverse_ok,
    forward_time_ms,
    reverse_time_ms,
    max_current_ma,
    target_angle_deg,
    actual_angle_deg,
    position_error_deg,
    result,
    failure_reason
)
SELECT
    ph.process_history_id,
    1,
    1,
    1250,
    1280,
    820.5,
    NULL,
    NULL,
    NULL,
    'PASS',
    NULL
FROM process_history AS ph
JOIN product_serial AS ps
    ON ps.product_serial_id = ph.product_serial_id
JOIN routing_step AS rs
    ON rs.routing_step_id = ph.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
WHERE ps.serial_no = 'BASIC-20260728-001'
  AND p.process_code = 'PROC-EOL';


SELECT
    etr.eol_test_result_id,
    ps.serial_no,
    product.item_code AS product_code,
    wo.work_order_no,
    p.process_name,
    etr.forward_ok,
    etr.reverse_ok,
    etr.forward_time_ms,
    etr.reverse_time_ms,
    etr.max_current_ma,
    etr.target_angle_deg,
    etr.actual_angle_deg,
    etr.position_error_deg,
    etr.result,
    etr.failure_reason,
    etr.tested_at
FROM eol_test_result AS etr
JOIN process_history AS ph
    ON ph.process_history_id = etr.process_history_id
JOIN product_serial AS ps
    ON ps.product_serial_id = ph.product_serial_id
JOIN work_order AS wo
    ON wo.work_order_id = ps.work_order_id
JOIN item AS product
    ON product.item_id = wo.product_item_id
JOIN routing_step AS rs
    ON rs.routing_step_id = ph.routing_step_id
JOIN process AS p
    ON p.process_id = rs.process_id
ORDER BY etr.tested_at DESC;

