"""Deterministic impact tracing. No LLM calls in this module - every number
here comes from plain SQL/Python over the dataset, which is what makes each
claim in the final report traceable back to specific record IDs.
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Exposure:
    """One order_line put at risk, and the record chain that explains why."""

    order_line_id: str
    customer_order_id: str
    customer_id: str
    customer_name: str
    customer_tier: str
    product_id: str
    product_name: str
    quantity: int
    requested_delivery_date: date
    order_status: str

    exposure_kind: str  # "pending_po" | "on_hand_stock"
    source_ids: list[str] = field(default_factory=list)  # PO/shipment/stock_lot ids, for citation

    original_ready_date: date | None = None  # shipment eta or PO expected date
    revised_ready_date: date | None = None  # after applying delay_days
    slip_days: int | None = None  # None = disruption confirmed but magnitude unstated
    urgency_score: float = 0.0


TIER_WEIGHT = {"vip": 30, "priority": 15, "standard": 0}


def _parse(d: str) -> date:
    return date.fromisoformat(d)


def _find_pending_pos_for_supplier(conn: sqlite3.Connection, supplier_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM purchase_orders WHERE supplier_id=? AND status IN ('open','in_transit')",
        (supplier_id,),
    ).fetchall()


def _find_pending_pos_for_product(conn: sqlite3.Connection, product_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM purchase_orders WHERE product_id=? AND status IN ('open','in_transit')",
        (product_id,),
    ).fetchall()


def _find_stock_lots_for_product(conn: sqlite3.Connection, product_id: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM stock_lots WHERE product_id=?", (product_id,)).fetchall()


def _find_shipments_for_carrier(conn: sqlite3.Connection, carrier: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM shipments WHERE carrier=? AND status != 'delivered'",
        (carrier,),
    ).fetchall()


def _order_lines_for_po(conn: sqlite3.Connection, po_id: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM order_lines WHERE purchase_order_id=?", (po_id,)).fetchall()


def _order_lines_for_stock_lot(conn: sqlite3.Connection, lot_id: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM order_lines WHERE stock_lot_id=?", (lot_id,)).fetchall()


def _shipment_for_po(conn: sqlite3.Connection, po_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM shipments WHERE purchase_order_id=? ORDER BY eta LIMIT 1", (po_id,)
    ).fetchone()


def _build_exposure(conn: sqlite3.Connection, ol: sqlite3.Row, kind: str, source_ids: list[str]) -> Exposure:
    co = conn.execute("SELECT * FROM customer_orders WHERE id=?", (ol["customer_order_id"],)).fetchone()
    cust = conn.execute("SELECT * FROM customers WHERE id=?", (co["customer_id"],)).fetchone()
    prod = conn.execute("SELECT * FROM products WHERE id=?", (ol["product_id"],)).fetchone()

    return Exposure(
        order_line_id=ol["id"],
        customer_order_id=co["id"],
        customer_id=cust["id"],
        customer_name=cust["name"],
        customer_tier=cust["tier"],
        product_id=prod["id"],
        product_name=prod["name"],
        quantity=ol["quantity"],
        requested_delivery_date=_parse(co["requested_delivery_date"]),
        order_status=co["status"],
        exposure_kind=kind,
        source_ids=source_ids,
    )


def find_exposed_order_lines(conn: sqlite3.Connection, entity_type: str, entity_id: str) -> list[Exposure]:
    """Given a resolved entity ("supplier"/"product"/"carrier", id), returns
    every order_line that depends on stock or shipments tied to it, with the
    record chain that justifies the exposure."""
    exposures: list[Exposure] = []
    seen_ol_ids: set[str] = set()

    def add_from_po(po: sqlite3.Row):
        shipment = _shipment_for_po(conn, po["id"])
        source = [po["id"]] + ([shipment["id"]] if shipment else [])
        for ol in _order_lines_for_po(conn, po["id"]):
            if ol["id"] in seen_ol_ids:
                continue
            seen_ol_ids.add(ol["id"])
            exp = _build_exposure(conn, ol, "pending_po", source)
            exp.original_ready_date = _parse(shipment["eta"]) if shipment else _parse(po["expected_delivery_date"])
            exposures.append(exp)

    def add_from_stock_lot(lot: sqlite3.Row):
        for ol in _order_lines_for_stock_lot(conn, lot["id"]):
            if ol["id"] in seen_ol_ids:
                continue
            seen_ol_ids.add(ol["id"])
            exposures.append(_build_exposure(conn, ol, "on_hand_stock", [lot["id"]]))

    if entity_type == "supplier":
        for po in _find_pending_pos_for_supplier(conn, entity_id):
            add_from_po(po)

    elif entity_type == "product":
        for po in _find_pending_pos_for_product(conn, entity_id):
            add_from_po(po)
        for lot in _find_stock_lots_for_product(conn, entity_id):
            add_from_stock_lot(lot)

    elif entity_type == "carrier":
        for shipment in _find_shipments_for_carrier(conn, entity_id):
            po = conn.execute(
                "SELECT * FROM purchase_orders WHERE id=?", (shipment["purchase_order_id"],)
            ).fetchone()
            if po is None or po["status"] not in ("open", "in_transit"):
                continue
            source = [po["id"], shipment["id"]]
            for ol in _order_lines_for_po(conn, po["id"]):
                if ol["id"] in seen_ol_ids:
                    continue
                seen_ol_ids.add(ol["id"])
                exp = _build_exposure(conn, ol, "pending_po", source)
                exp.original_ready_date = _parse(shipment["eta"])
                exposures.append(exp)

    return exposures


def apply_disruption(exposures: list[Exposure], delay_days: int | None, today: date) -> list[Exposure]:
    """Fills in revised dates, slip, and urgency score given the notice's
    stated delay (may be unknown for warehouse-incident/stock-loss notices)."""
    for exp in exposures:
        if exp.exposure_kind == "pending_po" and exp.original_ready_date is not None:
            if delay_days is not None:
                from datetime import timedelta

                exp.revised_ready_date = exp.original_ready_date + timedelta(days=delay_days)
                exp.slip_days = max(0, (exp.revised_ready_date - exp.requested_delivery_date).days)
            else:
                exp.slip_days = None  # disruption confirmed, magnitude not stated in the notice

        days_until_due = (exp.requested_delivery_date - today).days
        urgency = TIER_WEIGHT.get(exp.customer_tier, 0)
        urgency += max(0, 60 - days_until_due)  # sooner due date -> more urgent
        if exp.slip_days:
            urgency += exp.slip_days * 2
        elif exp.slip_days is None:
            urgency += 10  # unquantified risk still counts, but less than a confirmed slip
        if exp.exposure_kind == "on_hand_stock":
            urgency += 15  # stock already committed and now at risk, no lead time to fall back on
        exp.urgency_score = urgency

    return sorted(exposures, key=lambda e: e.urgency_score, reverse=True)
