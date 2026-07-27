CREATE TABLE item (item_id INTEGER PRIMARY KEY,
                   item_code TEXT NOT NULL UNIQUE,
                   item_name TEXT NOT NULL,
                   item_type TEXT NOT NULL CHECK (item_type IN ('PRODUCT', 'MATERIAL')),
                   is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)));


CREATE TABLE process (process_id INTEGER PRIMARY KEY,
                      process_code TEXT NOT NULL UNIQUE,
                      process_name TEXT NOT NULL,
                      process_type TEXT NOT NULL CHECK (process_type IN ('ASSEMBLY', 'INSPECTION', 'COMPLETION')));



CREATE TABLE routing_step (routing_step_id INTEGER PRIMARY KEY,
                           product_item_id INTEGER NOT NULL,
                           process_id INTEGER NOT NULL,
                           sequence_no INTEGER NOT NULL CHECK(sequence_no > 0),
                           is_required INTEGER NOT NULL DEFAULT 1 CHECK (is_required IN (0, 1)),
                           is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                           FOREIGN KEY (product_item_id) REFERENCES item (item_id),
                           FOREIGN KEY (process_id) REFERENCES process (process_id),
                           UNIQUE (product_item_id, sequence_no),
                           UNIQUE (product_item_id, process_id));


CREATE TABLE bom (bom_id INTEGER PRIMARY KEY,
                  product_item_id INTEGER NOT NULL,
                  material_item_id INTEGER NOT NULL CHECK (product_item_id <> material_item_id),
                  input_routing_step_id INTEGER NOT NULL,
                  required_qty INTEGER CHECK (required_qty > 0),
                  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (product_item_id) REFERENCES item(item_id),
                  FOREIGN KEY (material_item_id) REFERENCES item(item_id),
                  FOREIGN KEY (input_routing_step_id) REFERENCES routing_step(routing_step_id),
                  UNIQUE (product_item_id, material_item_id, input_routing_step_id));


CREATE TABLE material_lot (material_lot_id INTEGER PRIMARY KEY,
                           lot_no TEXT NOT NULL UNIQUE,
                           material_item_id INTEGER NOT NULL,
                           received_qty INTEGER NOT NULL CHECK (received_qty > 0),
                           received_date TEXT NOT NULL,
                           status TEXT NOT NULL DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'EXHAUSTED', 'BLOCKED')),
                           created_atTEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (material_item_id) REFERENCES item (item_id));
