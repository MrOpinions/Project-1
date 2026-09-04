"""Deterministic option generation for each affected order. Every option's
numbers (spare stock, dates) come from the dataset; cost/time trade-offs for
expediting are stated as explicit planning assumptions, not claimed as data.
"""

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from core.impact_engine import Exposure

# Planning assumptions for expediting - not drawn from data, stated plainly
# in the report as assumptions rather than measured facts.
EXPEDITE_RECOVERY_FRACTION = 0.6  # expediting recovers ~60% of a slip
EXPEDITE_COST_NOTE = "~2x normal freight cost (typical air-freight vs. ocean/ground upcharge)"


@dataclass
class ActionOption:
    kind: str  # expedite | part_ship | reallocate | notify_customer
    description: str
    trade_off: str
    new_estimate: date | None = None


def _spare_on_hand(conn: sqlite3.Connection, product_id: str, exclude_lot_ids: tuple[str, ...] = ()) -> int:
    """On-hand quantity for a product not already claimed by any order_line,
    optionally excluding specific lots (e.g. a lot that is itself the subject
    of a warehouse-incident notice, so it isn't counted as its own backup)."""
    lots = conn.execute("SELECT id, quantity_on_hand FROM stock_lots WHERE product_id=?", (product_id,)).fetchall()
    total = sum(l["quantity_on_hand"] for l in lots if l["id"] not in exclude_lot_ids)
    lot_ids = [l["id"] for l in lots if l["id"] not in exclude_lot_ids]
    if not lot_ids:
        return 0
    placeholders = ",".join("?" for _ in lot_ids)
    allocated = conn.execute(
        f"SELECT COALESCE(SUM(quantity),0) FROM order_lines WHERE stock_lot_id IN ({placeholders})",
        lot_ids,
    ).fetchone()[0]
    return max(0, total - allocated)


def generate_options_for_batch(
    conn: sqlite3.Connection, exposures: list[Exposure]
) -> list[tuple[list[ActionOption], int]]:
    """Generates options for a ranked batch of exposures, treating spare
    on-hand stock as a shared pool consumed in urgency order (exposures is
    expected pre-sorted, most urgent first) so two orders are never each
    shown the same spare units as independently available."""
    spare_pool: dict[str, int] = {}
    results = []
    for exp in exposures:
        if exp.product_id not in spare_pool:
            exclude = tuple(exp.source_ids) if exp.exposure_kind == "on_hand_stock" else ()
            spare_pool[exp.product_id] = _spare_on_hand(conn, exp.product_id, exclude)
        options, recommended = _generate_options(conn, exp, spare_pool)
        results.append((options, recommended))
    return results


def _generate_options(
    conn: sqlite3.Connection, exp: Exposure, spare_pool: dict[str, int]
) -> tuple[list[ActionOption], int]:
    """Returns (options, recommended_index). Consumes from spare_pool in place."""
    options: list[ActionOption] = []
    spare = spare_pool.get(exp.product_id, 0)

    if exp.exposure_kind == "pending_po":
        if exp.slip_days:  # confirmed slip > 0
            recovered_days = round(exp.slip_days * EXPEDITE_RECOVERY_FRACTION)
            new_slip = exp.slip_days - recovered_days
            new_est = exp.requested_delivery_date + timedelta(days=new_slip)
            options.append(ActionOption(
                kind="expedite",
                description=f"Expedite the remaining shipment; recovers an estimated {recovered_days} of the "
                            f"{exp.slip_days}-day slip.",
                trade_off=f"{EXPEDITE_COST_NOTE}; still arrives ~{new_slip}d late" if new_slip > 0
                          else f"{EXPEDITE_COST_NOTE}; arrives on time",
                new_estimate=new_est,
            ))

        if spare > 0:
            part_qty = min(spare, exp.quantity)
            options.append(ActionOption(
                kind="part_ship",
                description=f"Ship {part_qty} of {exp.quantity} now from unallocated on-hand stock; "
                            f"remainder follows once the delayed shipment arrives.",
                trade_off="No extra cost; customer still gets a split delivery and a second, later date "
                          "for the remaining units.",
                new_estimate=exp.revised_ready_date,
            ))
            spare_pool[exp.product_id] = spare - part_qty

        options.append(ActionOption(
            kind="reallocate",
            description="Reallocate stock committed to a lower-urgency order on the same product to "
                         "cover this order instead.",
            trade_off="Fixes this order but pushes the lower-urgency order back in the queue instead - "
                       "does not remove the shortage, only moves who absorbs it.",
        ))

        options.append(ActionOption(
            kind="notify_customer",
            description=f"Inform the customer of the revised date"
                        + (f" ({exp.revised_ready_date.isoformat()})" if exp.revised_ready_date else " once known")
                        + ".",
            trade_off="No cost, no recovery - simplest option when the slip is small or expediting/"
                      "reallocating isn't worth it.",
            new_estimate=exp.revised_ready_date,
        ))

        recommended = 0 if exp.slip_days and exp.customer_tier in ("vip", "priority") else (
            1 if spare > 0 else len(options) - 1
        )

    else:  # on_hand_stock at risk (e.g. warehouse incident)
        if spare >= exp.quantity:
            options.append(ActionOption(
                kind="reallocate",
                description=f"Cover this order from other unaffected on-hand stock of the same product "
                            f"({spare} units available elsewhere before this order).",
                trade_off="No cost if the incident is confirmed to affect only this specific lot.",
            ))
            spare_pool[exp.product_id] = spare - exp.quantity
        options.append(ActionOption(
            kind="notify_customer",
            description="Inform the customer that the stock backing their order may be affected, "
                        "pending confirmation of the incident's extent.",
            trade_off="No cost, but leaves the customer without a firm date until the warehouse "
                      "confirms what was actually lost.",
        ))
        recommended = 0  # reallocate if available, else notify - both land at index 0

    return options, recommended
