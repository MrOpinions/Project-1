"""Pulls structured candidate fields out of a free-text disruption notice.

This is the ONLY place the LLM is asked to read the raw notice. It is not
asked to reason about impact - only to extract what it plainly states, as
strict JSON. Everything downstream (resolving those mentions to real
records, and computing what they affect) is deterministic Python.
"""

from google.genai import types

from core.gemini_client import GENERATION_MODEL, get_client

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "mentions": {
            "type": "array",
            "description": (
                "Short phrases naming a specific company, supplier, carrier, "
                "product, or location the notice is about. Copy the wording "
                "used in the notice; do not invent names."
            ),
            "items": {"type": "string"},
        },
        "disruption_type": {
            "type": "string",
            "enum": ["production_halt", "shipment_delay", "warehouse_incident", "other"],
        },
        "delay_days": {
            "type": "integer",
            "description": "Number of days of delay explicitly stated, if any. Omit if not stated.",
        },
        "summary": {
            "type": "string",
            "description": "One sentence restating what the notice says, no added interpretation.",
        },
    },
    "required": ["mentions", "disruption_type", "summary"],
}

PROMPT = """You extract facts from a supply-chain disruption notice. Only report
what the text explicitly states. Do not guess company names, dates, or
quantities that are not written in the text. Do not add commentary.

Notice:
---
{notice}
---
"""


def extract(notice_text: str) -> dict:
    client = get_client()
    resp = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=PROMPT.format(notice=notice_text),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            temperature=0,
        ),
    )
    import json

    return json.loads(resp.text)
