"""Builds data/distributor.db from schema.sql with a small, hand-crafted dataset.

The data is hand-crafted rather than randomly generated so that every
supplier -> purchase_order -> shipment -> stock_lot -> order_line -> customer_order
chain is known and verifiable by hand. Dates are relative to the day this
script is run, so the dataset always reads as "current" relative to itself.

Run: python data/seed_data.py
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "distributor.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

TODAY = date.today()


def d(offset_days: int) -> str:
    """ISO date string `offset_days` from today (negative = past)."""
    return (TODAY + timedelta(days=offset_days)).isoformat()


SUPPLIERS = [
    ("S1", "Coastal Gasket Works", "Chennai, India", "gaskets", "reliable"),
    ("S2", "Nordic Circuit Co", "Gothenburg, Sweden", "electronics", "reliable"),
    ("S3", "Redline Steel Ltd", "Pittsburgh, USA", "steel components", "frequent delays"),
    ("S4", "Pacific Resin Supply", "Osaka, Japan", "adhesives and resins", "reliable"),
    ("S5", "Delta Packaging Inc", "Columbus, USA", "packaging materials", "reliable"),
    ("S6", "Sunrise Textiles Co", "Dhaka, Bangladesh", "textiles", "occasional delays"),
]

PRODUCTS = [
    ("P1", "GSK-040", "Rubber Gasket 40mm", "gaskets", "each"),
    ("P2", "GSK-060", "Rubber Gasket 60mm", "gaskets", "each"),
    ("P3", "CB-REVC", "Circuit Board Rev C", "electronics", "each"),
    ("P4", "STL-L200", "Steel Bracket L-200", "steel components", "each"),
    ("P5", "STL-L350", "Steel Bracket L-350", "steel components", "each"),
    ("P6", "RES-5L", "Industrial Resin 5L", "adhesives", "drum"),
    ("P7", "BOX-LG", "Corrugated Box Large", "packaging", "each"),
    ("P8", "BOX-SM", "Corrugated Box Small", "packaging", "each"),
    ("P9", "TXT-CWR", "Cotton Wrap Roll", "textiles", "roll"),
    ("P10", "CB-REVD", "Circuit Board Rev D", "electronics", "each"),
]

# id, supplier_id, product_id, quantity, order_date_offset, expected_delivery_offset, status
PURCHASE_ORDERS = [
    ("PO1", "S1", "P1", 500, -20, 3, "in_transit"),
    ("PO2", "S1", "P2", 300, -15, 7, "in_transit"),
    ("PO3", "S2", "P3", 200, -30, -5, "received"),
    ("PO4", "S3", "P4", 400, -10, 10, "in_transit"),
    ("PO5", "S3", "P5", 150, -8, 12, "open"),
    ("PO6", "S4", "P6", 100, -25, -2, "received"),
    ("PO7", "S5", "P7", 1000, -5, 9, "in_transit"),
    ("PO8", "S6", "P9", 250, -12, 6, "in_transit"),
    ("PO9", "S2", "P10", 180, -6, 14, "open"),
    ("PO10", "S1", "P1", 200, -40, -20, "received"),
]

# id, purchase_order_id, carrier, origin, destination, departure_offset, eta_offset, status, tracking_ref
SHIPMENTS = [
    ("SH1", "PO1", "BlueWave Logistics", "Chennai", "Warehouse", -2, 3, "in_transit", "BW-1001"),
    ("SH2", "PO2", "BlueWave Logistics", "Chennai", "Warehouse", None, 7, "pending", "BW-1002"),
    ("SH3", "PO4", "TransCargo Freight", "Pittsburgh", "Warehouse", -3, 10, "in_transit", "TC-2044"),
    ("SH4", "PO7", "Heartland Trucking", "Columbus", "Warehouse", -1, 9, "in_transit", "HT-3390"),
    ("SH5", "PO8", "OceanLink Shipping", "Dhaka", "Warehouse", -10, 6, "in_transit", "OL-4471"),
]

# id, product_id, supplier_id, quantity_on_hand, warehouse_location, received_date_offset
STOCK_LOTS = [
    ("SL1", "P1", "S1", 80, "WH-A", -18),
    ("SL2", "P3", "S2", 150, "WH-B", -5),
    ("SL3", "P6", "S4", 60, "WH-C", -2),
    ("SL4", "P8", "S5", 500, "WH-D", -15),
    ("SL5", "P9", "S6", 20, "WH-D", -30),
]

CUSTOMERS = [
    ("C1", "Acme Manufacturing", "vip", "Detroit, USA"),
    ("C2", "BrightHome Appliances", "priority", "Austin, USA"),
    ("C3", "Coastal Builders Co", "standard", "Miami, USA"),
    ("C4", "Delta Auto Parts", "priority", "Cleveland, USA"),
    ("C5", "EverGreen Foods Packaging", "standard", "Chicago, USA"),
    ("C6", "FastTrack Logistics Hub", "standard", "Memphis, USA"),
    ("C7", "Grandview Electronics", "vip", "San Jose, USA"),
    ("C8", "Harbor Textiles Retail", "standard", "Newark, USA"),
]

# id, customer_id, order_date_offset, requested_delivery_offset, status
CUSTOMER_ORDERS = [
    ("CO1", "C1", -5, 4, "allocated"),
    ("CO2", "C4", -3, 8, "allocated"),
    ("CO3", "C3", -1, 12, "allocated"),
    ("CO4", "C6", -2, 2, "allocated"),
    ("CO5", "C7", -4, 20, "allocated"),
    ("CO6", "C2", -6, 3, "allocated"),
    ("CO7", "C1", -7, 9, "allocated"),
    ("CO8", "C4", -2, 25, "allocated"),
    ("CO9", "C5", -1, 5, "allocated"),
    ("CO10", "C8", -3, 8, "allocated"),
    ("CO11", "C2", -4, 11, "allocated"),
    ("CO12", "C3", -2, 4, "allocated"),
    ("CO13", "C5", 0, 10, "pending"),
    ("CO14", "C6", -1, 3, "allocated"),
    ("CO15", "C7", 0, 6, "pending"),
]

# id, customer_order_id, product_id, quantity, stock_lot_id, purchase_order_id
ORDER_LINES = [
    ("OL1", "CO1", "P1", 300, None, "PO1"),
    ("OL2", "CO2", "P2", 150, None, "PO2"),
    ("OL3", "CO3", "P1", 100, None, "PO1"),
    ("OL4", "CO4", "P1", 50, "SL1", None),
    ("OL5", "CO5", "P10", 100, None, "PO9"),
    ("OL6", "CO6", "P3", 80, "SL2", None),
    ("OL7", "CO7", "P4", 200, None, "PO4"),
    ("OL8", "CO8", "P5", 100, None, "PO5"),
    ("OL9", "CO9", "P6", 40, "SL3", None),
    ("OL10", "CO10", "P9", 100, None, "PO8"),
    ("OL11", "CO11", "P7", 200, None, "PO7"),
    ("OL12", "CO12", "P8", 150, "SL4", None),
    ("OL13", "CO13", "P6", 15, "SL3", None),
    ("OL14", "CO14", "P9", 5, "SL5", None),
    ("OL15", "CO15", "P3", 50, "SL2", None),
]


def build():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())

    conn.executemany("INSERT INTO suppliers VALUES (?,?,?,?,?)", SUPPLIERS)
    conn.executemany("INSERT INTO products VALUES (?,?,?,?,?)", PRODUCTS)
    conn.executemany(
        "INSERT INTO purchase_orders VALUES (?,?,?,?,?,?,?)",
        [(pid, sup, prod, qty, d(od), d(ed), status) for pid, sup, prod, qty, od, ed, status in PURCHASE_ORDERS],
    )
    conn.executemany(
        "INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (sid, po, carrier, origin, dest, d(dep) if dep is not None else None, d(eta), status, ref)
            for sid, po, carrier, origin, dest, dep, eta, status, ref in SHIPMENTS
        ],
    )
    conn.executemany(
        "INSERT INTO stock_lots VALUES (?,?,?,?,?,?)",
        [(sid, prod, sup, qty, wh, d(rd)) for sid, prod, sup, qty, wh, rd in STOCK_LOTS],
    )
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?)", CUSTOMERS)
    conn.executemany(
        "INSERT INTO customer_orders VALUES (?,?,?,?,?)",
        [(cid, cust, d(od), d(rd), status) for cid, cust, od, rd, status in CUSTOMER_ORDERS],
    )
    conn.executemany("INSERT INTO order_lines VALUES (?,?,?,?,?,?)", ORDER_LINES)

    conn.commit()
    conn.close()
    print(f"Seeded {DB_PATH} (today = {TODAY.isoformat()})")


if __name__ == "__main__":
    build()
