-- Distributor operations schema.
-- suppliers -> purchase_orders -> shipments -> stock_lots -> order_lines -> customer_orders -> customers

CREATE TABLE suppliers (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    location        TEXT NOT NULL,
    category        TEXT NOT NULL,        -- what they supply, e.g. "gaskets", "electronics"
    reliability     TEXT NOT NULL         -- free-text note, e.g. "reliable", "frequent delays"
);

CREATE TABLE products (
    id              TEXT PRIMARY KEY,
    sku             TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,
    unit            TEXT NOT NULL
);

CREATE TABLE purchase_orders (
    id                      TEXT PRIMARY KEY,
    supplier_id             TEXT NOT NULL REFERENCES suppliers(id),
    product_id              TEXT NOT NULL REFERENCES products(id),
    quantity                INTEGER NOT NULL,
    order_date              TEXT NOT NULL,
    expected_delivery_date  TEXT NOT NULL,
    status                  TEXT NOT NULL   -- open | in_transit | received | cancelled
);

CREATE TABLE shipments (
    id                  TEXT PRIMARY KEY,
    purchase_order_id   TEXT NOT NULL REFERENCES purchase_orders(id),
    carrier             TEXT NOT NULL,
    origin              TEXT NOT NULL,
    destination         TEXT NOT NULL,
    departure_date      TEXT,
    eta                 TEXT NOT NULL,
    status              TEXT NOT NULL,      -- pending | in_transit | delayed | delivered
    tracking_ref        TEXT NOT NULL
);

-- Stock physically on hand in the warehouse (already received).
CREATE TABLE stock_lots (
    id                  TEXT PRIMARY KEY,
    product_id          TEXT NOT NULL REFERENCES products(id),
    supplier_id         TEXT NOT NULL REFERENCES suppliers(id),
    quantity_on_hand    INTEGER NOT NULL,
    warehouse_location  TEXT NOT NULL,
    received_date       TEXT NOT NULL
);

CREATE TABLE customers (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    tier        TEXT NOT NULL,      -- standard | priority | vip
    location    TEXT NOT NULL
);

CREATE TABLE customer_orders (
    id                          TEXT PRIMARY KEY,
    customer_id                 TEXT NOT NULL REFERENCES customers(id),
    order_date                  TEXT NOT NULL,
    requested_delivery_date     TEXT NOT NULL,
    status                      TEXT NOT NULL   -- pending | allocated | shipped | fulfilled
);

-- Each line allocates its quantity to EITHER on-hand stock (stock_lot_id set)
-- OR an incoming purchase order not yet received (purchase_order_id set), never both.
CREATE TABLE order_lines (
    id                      TEXT PRIMARY KEY,
    customer_order_id       TEXT NOT NULL REFERENCES customer_orders(id),
    product_id              TEXT NOT NULL REFERENCES products(id),
    quantity                INTEGER NOT NULL,
    stock_lot_id            TEXT REFERENCES stock_lots(id),
    purchase_order_id       TEXT REFERENCES purchase_orders(id)
);
