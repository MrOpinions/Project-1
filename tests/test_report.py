"""Pure-Python tests for the narrative grounding check - no Gemini calls.

This is the safety net that stops a hallucinated citation from reaching the
user: it scans an AI-written narrative for anything that looks like a record
ID and confirms every one of them was actually part of the verified facts
handed to the model. These tests exercise that check directly, independent
of whether the AI call itself is ever reached.

Run: python -m pytest tests/test_report.py -v
"""

from core.report import check_narrative_grounding


def test_narrative_with_only_grounded_ids_passes():
    grounding_ids = {"CO1", "CO2", "PO1", "SH1"}
    text = "Order CO1 is the most urgent, sourced from PO1 via SH1. CO2 is also affected."

    all_grounded, cited = check_narrative_grounding(text, grounding_ids)

    assert all_grounded is True
    assert cited == ["CO1", "CO2", "PO1", "SH1"]


def test_narrative_citing_an_unverified_id_is_rejected():
    """CO9 was never part of this report's verified facts - a model that
    invents it must be caught, not trusted."""
    grounding_ids = {"CO1", "PO1", "SH1"}
    text = "Order CO1 is affected, and so is CO9 which is unusually urgent."

    all_grounded, cited = check_narrative_grounding(text, grounding_ids)

    assert all_grounded is False
    assert cited == ["CO1", "CO9"]


def test_narrative_with_no_ids_mentioned_trivially_passes():
    grounding_ids = {"CO1", "PO1"}
    text = "This notice does not map to anything currently pending."

    all_grounded, cited = check_narrative_grounding(text, grounding_ids)

    assert all_grounded is True
    assert cited == []


def test_narrative_citing_only_out_of_scope_ids_is_rejected():
    """Every mentioned ID is wrong - not just partially grounded."""
    grounding_ids = {"CO1"}
    text = "The affected orders are PO99 and SH42."

    all_grounded, cited = check_narrative_grounding(text, grounding_ids)

    assert all_grounded is False
    assert cited == ["PO99", "SH42"]
