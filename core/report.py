"""Assembles the full pipeline: notice text -> extraction -> resolution ->
impact -> options -> a grounded report. The narrative-writing LLM call is
handed only facts already computed in Python and is checked afterward for
citations it wasn't given.
"""

import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date

from google.genai import types

from core.actions import ActionOption, generate_options_for_batch
from core.db import connect
from core.extraction import extract
from core.gemini_client import GENERATION_MODEL, get_client
from core.impact_engine import Exposure, apply_disruption, find_exposed_order_lines
from core.resolution import Resolution, resolve_mentions

ID_PATTERN = re.compile(r"\b(?:CO|PO|SH|SL)\d+\b")


@dataclass
class AffectedOrderReport:
    exposure: Exposure
    options: list[ActionOption]
    recommended_index: int


@dataclass
class ImpactReport:
    notice_summary: str
    disruption_type: str
    resolved_entities: list[Resolution]
    unresolved_mentions: list[str]
    affected_orders: list[AffectedOrderReport]
    no_impact: bool
    narrative: str
    grounding_ids: set


def _entity_type_and_id(entity_key: str) -> tuple[str, str]:
    t, _, eid = entity_key.partition(":")
    return t, eid


def _gather_exposures(conn: sqlite3.Connection, resolutions: list[Resolution]) -> list[Exposure]:
    seen: dict[str, Exposure] = {}
    for r in resolutions:
        if r.entity_key is None:
            continue
        etype, eid = _entity_type_and_id(r.entity_key)
        if etype not in ("supplier", "product", "carrier"):
            continue  # e.g. a customer name was mentioned - not a disruption source
        for exp in find_exposed_order_lines(conn, etype, eid):
            seen[exp.order_line_id] = exp  # de-dup if multiple mentions hit the same entity
    return list(seen.values())


def _grounding_ids(exposures: list[Exposure]) -> set[str]:
    ids: set[str] = set()
    for e in exposures:
        ids.update({e.order_line_id, e.customer_order_id, e.customer_id, e.product_id})
        ids.update(e.source_ids)
    return ids


NARRATIVE_PROMPT = """You are writing an impact-assessment narrative for a warehouse
operator. Use ONLY the facts in the JSON below - do not add any order ID,
customer name, product, date, or number that is not present in it. Do not
speculate about causes or outcomes beyond what is given. Write 3-5 sentences:
what the notice reported, what it affects, and the overall urgency picture.
End by naming the single most urgent order by its ID.

FACTS:
{facts}
"""


def _facts_payload(disruption_type: str, notice_summary: str, affected: list[AffectedOrderReport]) -> dict:
    return {
        "notice_summary": notice_summary,
        "disruption_type": disruption_type,
        "affected_order_count": len(affected),
        "affected_orders": [
            {
                "order_id": a.exposure.customer_order_id,
                "customer": a.exposure.customer_name,
                "tier": a.exposure.customer_tier,
                "product": a.exposure.product_name,
                "quantity": a.exposure.quantity,
                "requested_delivery_date": a.exposure.requested_delivery_date.isoformat(),
                "slip_days": a.exposure.slip_days,
                "recommended_action": a.options[a.recommended_index].kind if a.options else None,
            }
            for a in affected
        ],
    }


def _write_narrative(facts: dict, grounding_ids: set[str]) -> str:
    client = get_client()
    resp = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=NARRATIVE_PROMPT.format(facts=json.dumps(facts, indent=2)),
        config=types.GenerateContentConfig(temperature=0),
    )
    text = resp.text.strip()

    mentioned_ids = set(ID_PATTERN.findall(text))
    ungrounded = mentioned_ids - grounding_ids
    if ungrounded:
        ids_line = ", ".join(sorted(f["order_id"] for f in facts["affected_orders"]))
        text = (
            f"{facts['notice_summary']} This affects {facts['affected_order_count']} order(s): {ids_line}. "
            "(Narrative generation cited an ID outside the verified data and was replaced with this "
            "fact-only summary.)"
        )
    return text


def build_report(notice_text: str, today: date | None = None) -> ImpactReport:
    today = today or date.today()
    conn = connect()

    fields = extract(notice_text)
    resolutions = resolve_mentions(fields.get("mentions", []))
    unresolved = [r.mention for r in resolutions if r.entity_key is None]

    exposures = _gather_exposures(conn, resolutions)

    if not exposures:
        return ImpactReport(
            notice_summary=fields.get("summary", ""),
            disruption_type=fields.get("disruption_type", "other"),
            resolved_entities=resolutions,
            unresolved_mentions=unresolved,
            affected_orders=[],
            no_impact=True,
            narrative=(
                f"{fields.get('summary', 'Notice reviewed.')} No open purchase order, in-transit shipment, "
                "or on-hand stock in the system is currently exposed to this. No action needed."
            ),
            grounding_ids=set(),
        )

    delay_days = fields.get("delay_days") if fields.get("disruption_type") != "warehouse_incident" else None
    exposures = apply_disruction_safe(exposures, delay_days, today)
    batch = generate_options_for_batch(conn, exposures)
    affected = [
        AffectedOrderReport(exposure=e, options=opts, recommended_index=rec)
        for e, (opts, rec) in zip(exposures, batch)
    ]

    grounding_ids = _grounding_ids(exposures)
    facts = _facts_payload(fields.get("disruption_type", "other"), fields.get("summary", ""), affected)
    narrative = _write_narrative(facts, grounding_ids)

    return ImpactReport(
        notice_summary=fields.get("summary", ""),
        disruption_type=fields.get("disruption_type", "other"),
        resolved_entities=resolutions,
        unresolved_mentions=unresolved,
        affected_orders=affected,
        no_impact=False,
        narrative=narrative,
        grounding_ids=grounding_ids,
    )


def apply_disruction_safe(exposures, delay_days, today):
    return apply_disruption(exposures, delay_days, today)
