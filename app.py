import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from core.report import build_report

app = Flask(__name__)

SAMPLE_NOTICES_PATH = Path(__file__).parent / "data" / "sample_notices.json"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/samples")
def samples():
    return jsonify(json.loads(SAMPLE_NOTICES_PATH.read_text()))


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/api/analyze", methods=["POST"])
def analyze():
    notice = (request.get_json(silent=True) or {}).get("notice", "").strip()
    if not notice:
        return jsonify({"error": "notice text is required"}), 400

    try:
        report = build_report(notice)
    except Exception as exc:  # Gemini outage/timeout/etc - fail with a clear message, not a stack trace
        return jsonify({
            "error": "The analysis could not complete - the Gemini API may be temporarily unavailable. "
                     "Please try again.",
            "detail": str(exc),
        }), 502

    return jsonify({
        "no_impact": report.no_impact,
        "disruption_type": report.disruption_type,
        "notice_summary": report.notice_summary,
        "narrative": report.narrative,
        "resolved_entities": [
            {"mention": r.mention, "entity_key": r.entity_key, "score": round(r.score, 3), "method": r.method}
            for r in report.resolved_entities
        ],
        "unresolved_mentions": report.unresolved_mentions,
        "affected_orders": [
            {
                "order_id": a.exposure.customer_order_id,
                "customer": a.exposure.customer_name,
                "tier": a.exposure.customer_tier,
                "product": a.exposure.product_name,
                "quantity": a.exposure.quantity,
                "requested_delivery_date": a.exposure.requested_delivery_date.isoformat(),
                "exposure_kind": a.exposure.exposure_kind,
                "source_ids": a.exposure.source_ids,
                "original_ready_date": a.exposure.original_ready_date.isoformat() if a.exposure.original_ready_date else None,
                "revised_ready_date": a.exposure.revised_ready_date.isoformat() if a.exposure.revised_ready_date else None,
                "slip_days": a.exposure.slip_days,
                "urgency_score": round(a.exposure.urgency_score, 1),
                "options": [
                    {
                        "kind": o.kind,
                        "description": o.description,
                        "trade_off": o.trade_off,
                        "new_estimate": o.new_estimate.isoformat() if o.new_estimate else None,
                    }
                    for o in a.options
                ],
                "recommended_index": a.recommended_index,
            }
            for a in report.affected_orders
        ],
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
