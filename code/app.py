"""
RiskManager — Web Dashboard
Interactive UI for reviewing chargeback analysis results.

Usage:
    cd code
    python app.py
    # Open http://127.0.0.1:5000 in your browser
"""

import csv
import json
from datetime import date, datetime
from pathlib import Path

from flask import Flask, render_template, jsonify, request

REPO_ROOT = Path(__file__).parent.parent
app = Flask(__name__, template_folder=str(REPO_ROOT / "code" / "templates"))


def load_csv(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_merchant_history() -> dict:
    path = REPO_ROOT / "dataset" / "merchant_history.csv"
    rows = load_csv(path)
    return {r["merchant_id"]: r for r in rows}


def dispute_age(txn_date_str: str) -> int:
    try:
        txn = datetime.strptime(txn_date_str, "%Y-%m-%d").date()
        return (date.today() - txn).days
    except (TypeError, ValueError):
        return -1


def enrich_cases(cases: list, predictions: list, merchant_history: dict) -> list:
    """Merge case data with predictions and merchant history into a single list."""
    pred_map = {r["case_id"]: r for r in predictions}
    enriched = []

    for case in cases:
        cid = case["case_id"]
        pred = pred_map.get(cid, {})
        mid = case.get("merchant_id", "")
        merchant = merchant_history.get(mid, {})

        age = dispute_age(case.get("transaction_date", ""))

        # Parse risk flags
        flags_raw = pred.get("risk_flags", "none")
        flags = [f.strip() for f in flags_raw.split(";") if f.strip() and f.strip() != "none"]

        # Parse evidence items
        evidence_raw = case.get("evidence_items", "")
        evidence_list = []
        if evidence_raw:
            for i, item in enumerate(evidence_raw.split("|"), 1):
                item = item.strip()
                if ":" in item:
                    etype, desc = item.split(":", 1)
                    evidence_list.append({
                        "id": f"ev_{i}",
                        "type": etype.strip(),
                        "description": desc.strip()
                    })

        enriched.append({
            "case_id": cid,
            "merchant_id": mid,
            "amount": case.get("amount", "0"),
            "original_amount": case.get("original_amount", "0"),
            "currency": case.get("currency", "INR"),
            "transaction_date": case.get("transaction_date", "N/A"),
            "payment_method": case.get("payment_method", "N/A"),
            "reason_code": case.get("reason_code", "N/A"),
            "merchant_narrative": case.get("merchant_narrative", ""),
            "dispute_age_days": age,
            "decision": pred.get("decision", "pending"),
            "evidence_sufficiency": pred.get("evidence_sufficiency", "unknown"),
            "risk_flags": flags,
            "reason": pred.get("reason", "Not yet analyzed."),
            "confidence": float(pred.get("confidence", 0)),
            "cited_evidence_ids": pred.get("cited_evidence_ids", "none"),
            "evidence_items": evidence_list,
            "chargeback_rate_90d": merchant.get("chargeback_rate_90d", "N/A"),
            "prior_contest_win_rate": merchant.get("prior_contest_win_rate", "N/A"),
        })

    return enriched


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/cases")
def api_cases():
    dataset = request.args.get("dataset", "demo")
    cases_path = REPO_ROOT / "dataset" / dataset / "cases.csv"
    output_path = REPO_ROOT / "dataset" / dataset / "output.csv"

    cases = load_csv(cases_path)
    predictions = load_csv(output_path)
    merchant_history = load_merchant_history()

    enriched = enrich_cases(cases, predictions, merchant_history)

    # Summary stats
    total = len(enriched)
    decisions = {}
    total_confidence = 0
    flag_counts = {}
    for c in enriched:
        d = c["decision"]
        decisions[d] = decisions.get(d, 0) + 1
        total_confidence += c["confidence"]
        for f in c["risk_flags"]:
            flag_counts[f] = flag_counts.get(f, 0) + 1

    avg_conf = (total_confidence / total) if total > 0 else 0

    return jsonify({
        "cases": enriched,
        "summary": {
            "total": total,
            "decisions": decisions,
            "avg_confidence": round(avg_conf, 2),
            "flag_counts": flag_counts,
            "dataset": dataset,
            "generated_at": date.today().isoformat(),
        }
    })


if __name__ == "__main__":
    print("\n  RiskManager Dashboard")
    print("  Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, port=5000)
