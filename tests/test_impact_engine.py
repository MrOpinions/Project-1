"""Pure-Python tests against the seeded dataset - no Gemini calls, fast to run.

Run: python -m pytest tests/test_impact_engine.py -v
"""

import sqlite3
from datetime import date
from pathlib import Path

from core.actions import generate_options_for_batch
from core.db import connect
from core.impact_engine import apply_disruption, find_exposed_order_lines

SCHEMA_PATH = Path(__file__).parent.parent / "data" / "schema.sql"


def test_supplier_disruption_exposes_pending_pos_not_on_hand_stock():
    """Coastal Gasket Works (S1): CO1/CO2/CO3 depend on its incoming POs and
    should be exposed. CO4 draws from on-hand stock (SL1, from an older,
    already-received PO) and must NOT be exposed by this disruption."""
    conn = connect()
    exposures = find_exposed_order_lines(conn, "supplier", "S1")
    exposed_orders = {e.customer_order_id for e in exposures}

    assert {"CO1", "CO2", "CO3"} <= exposed_orders
    assert "CO4" not in exposed_orders


def test_supplier_with_nothing_pending_has_no_exposure():
    """Pacific Resin Supply (S4): its only PO (PO6) is already received, so
    a disruption notice about them should trace to zero exposed orders."""
    conn = connect()
    exposures = find_exposed_order_lines(conn, "supplier", "S4")
    assert exposures == []


def test_slip_days_computed_from_delay_and_due_date():
    conn = connect()
    exposures = find_exposed_order_lines(conn, "supplier", "S1")
    exposures = apply_disruption(exposures, delay_days=21, today=date.today())

    by_id = {e.customer_order_id: e for e in exposures}
    # PO1/SH1 eta = today+3, +21 delay -> ready today+24. CO1 due today+4 -> slip 20.
    assert by_id["CO1"].slip_days == 20
    # CO3 due today+12, same shipment -> slip 12.
    assert by_id["CO3"].slip_days == 12


def test_warehouse_incident_flags_stock_backed_orders_without_fabricating_a_delay():
    conn = connect()
    exposures = find_exposed_order_lines(conn, "product", "P6")
    exposures = apply_disruption(exposures, delay_days=None, today=date.today())

    assert {"CO9", "CO13"} == {e.customer_order_id for e in exposures}
    for e in exposures:
        assert e.slip_days is None  # magnitude genuinely unstated - must not be guessed


def test_spare_stock_not_double_counted_across_orders_in_same_batch():
    """CO1 and CO3 both could draw on the same 30 spare units of P1 (SL1).
    Once CO1 (higher urgency) is offered a part-ship option consuming that
    spare stock, CO3 must not also be offered the same units as available."""
    conn = connect()
    exposures = find_exposed_order_lines(conn, "supplier", "S1")
    exposures = apply_disruption(exposures, delay_days=21, today=date.today())
    batch = generate_options_for_batch(conn, exposures)

    by_id = {e.customer_order_id: opts for e, (opts, _) in zip(exposures, batch)}
    co1_part_ship = next((o for o in by_id["CO1"] if o.kind == "part_ship"), None)
    co3_part_ship = next((o for o in by_id["CO3"] if o.kind == "part_ship"), None)

    assert co1_part_ship is not None
    assert co3_part_ship is None  # spare already claimed by the more urgent order


def test_unrelated_entity_type_produces_no_exposure():
    conn = connect()
    assert find_exposed_order_lines(conn, "customer", "C1") == []


def test_recommended_index_points_at_part_ship_when_delay_unstated_but_spare_exists():
    """Regression: Coastal Gasket Works (S1) disrupted with no stated delay
    magnitude means slip_days is None for its pending-PO exposures, so
    "expedite" is never offered. CO1 and CO3 both draw on product P1, which
    has spare on-hand stock (SL1), so part_ship should be offered and
    recommended - previously recommended was hardcoded to index 1, which
    silently pointed at "reallocate" instead once "expedite" dropped out of
    the options list."""
    conn = connect()
    exposures = find_exposed_order_lines(conn, "supplier", "S1")
    exposures = apply_disruption(exposures, delay_days=None, today=date.today())
    batch = generate_options_for_batch(conn, exposures)

    co1_index = next(i for i, e in enumerate(exposures) if e.customer_order_id == "CO1")
    options, recommended = batch[co1_index]
    assert options[recommended].kind == "part_ship"


def _minimal_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute("INSERT INTO suppliers VALUES ('S1','Test Supplier','Nowhere','widgets','reliable')")
    conn.execute("INSERT INTO products VALUES ('P1','SKU-1','Widget','widgets','each')")
    conn.execute(
        "INSERT INTO purchase_orders VALUES ('PO1','S1','P1',100,'2026-01-01','2026-02-01','in_transit')"
    )
    conn.execute("INSERT INTO customers VALUES ('C1','Test Customer','standard','Nowhere')")
    return conn


def test_already_fulfilled_order_is_not_reported_as_affected():
    """An order_line can reference a PO that later gets disrupted, but if the
    customer order already shows fulfilled/shipped, the disruption to its
    source PO no longer affects a delivery that already happened - it must
    not appear in the exposure list."""
    conn = _minimal_conn()
    conn.execute(
        "INSERT INTO customer_orders VALUES ('CO1','C1','2026-01-01','2026-01-15','fulfilled')"
    )
    conn.execute("INSERT INTO order_lines VALUES ('OL1','CO1','P1',10,NULL,'PO1')")

    exposures = find_exposed_order_lines(conn, "supplier", "S1")
    assert exposures == []


def test_pending_order_on_same_po_is_still_reported():
    conn = _minimal_conn()
    conn.execute(
        "INSERT INTO customer_orders VALUES ('CO2','C1','2026-01-01','2026-01-15','allocated')"
    )
    conn.execute("INSERT INTO order_lines VALUES ('OL2','CO2','P1',10,NULL,'PO1')")

    exposures = find_exposed_order_lines(conn, "supplier", "S1")
    assert {e.customer_order_id for e in exposures} == {"CO2"}
