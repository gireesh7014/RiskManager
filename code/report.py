"""
Audit Trail Report Generator — produces a self-contained HTML report
from the pipeline's output CSV + the original cases CSV.

Designed for the demo video: color-coded decisions, risk flag badges,
confidence bars, dispute-age indicators, and a top-level dashboard.

Usage:
    python code/report.py --cases dataset/dev/cases.csv --output dataset/dev/output.csv

Generates: dataset/dev/audit_report.html (same directory as the output CSV).
"""

import argparse
import csv
import html
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

DECISION_COLORS = {
    "contest": ("#10b981", "#065f46", "✓"),        # green
    "accept_liability": ("#ef4444", "#7f1d1d", "✗"),  # red
    "manual_review": ("#f59e0b", "#78350f", "⚠"),    # amber
}

FLAG_COLORS = {
    "amount_anomaly": "#f43f5e",
    "merchant_repeat_pattern": "#8b5cf6",
    "temporal_anomaly": "#06b6d4",
    "evidence_incomplete_for_reason_code": "#f97316",
    "narrative_contradicts_transaction": "#ec4899",
    "prompt_injection_attempt": "#dc2626",
    "domain_or_channel_mismatch": "#6366f1",
    "manual_review_required": "#94a3b8",
    "none": "#374151",
}


def load_csv(path: Path) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def confidence_bar(value: float) -> str:
    pct = int(float(value) * 100)
    if pct >= 80:
        color = "#10b981"
    elif pct >= 50:
        color = "#f59e0b"
    else:
        color = "#ef4444"
    return f'''<div class="conf-bar"><div class="conf-fill" style="width:{pct}%;background:{color}"></div><span class="conf-label">{pct}%</span></div>'''


def flag_badges(flags_str: str) -> str:
    flags = [f.strip() for f in flags_str.split(";") if f.strip()]
    badges = []
    for f in flags:
        color = FLAG_COLORS.get(f, "#374151")
        label = f.replace("_", " ")
        badges.append(f'<span class="flag-badge" style="background:{color}">{html.escape(label)}</span>')
    return " ".join(badges)


def dispute_age_indicator(txn_date_str: str) -> str:
    try:
        from datetime import datetime
        txn = datetime.strptime(txn_date_str, "%Y-%m-%d").date()
        age = (date.today() - txn).days
        if age > 120:
            color, label = "#ef4444", f"{age}d ⚠ STALE"
        elif age > 90:
            color, label = "#f59e0b", f"{age}d"
        else:
            color, label = "#10b981", f"{age}d"
        return f'<span class="age-tag" style="color:{color}">{label}</span>'
    except (TypeError, ValueError):
        return '<span class="age-tag" style="color:#94a3b8">n/a</span>'


def generate_report(cases: list, predictions: list, output_path: Path) -> Path:
    pred_map = {r["case_id"]: r for r in predictions}
    case_map = {r["case_id"]: r for r in cases}

    # Dashboard stats
    total = len(predictions)
    decision_counts = {}
    for r in predictions:
        d = r.get("decision", "unknown")
        decision_counts[d] = decision_counts.get(d, 0) + 1

    flag_counts = {}
    for r in predictions:
        for f in r.get("risk_flags", "none").split(";"):
            f = f.strip()
            if f and f != "none":
                flag_counts[f] = flag_counts.get(f, 0) + 1

    avg_confidence = 0
    if predictions:
        confs = []
        for r in predictions:
            try:
                confs.append(float(r.get("confidence", 0)))
            except (TypeError, ValueError):
                pass
        avg_confidence = sum(confs) / len(confs) if confs else 0

    report_path = output_path.parent / "audit_report.html"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chargeback Audit Trail — Risk Manager Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    line-height: 1.6;
    min-height: 100vh;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
  header {{
    text-align: center;
    padding: 3rem 0 2rem;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 2rem;
  }}
  header h1 {{
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
  }}
  header p {{ color: #94a3b8; font-size: 0.95rem; }}
  .dashboard {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2.5rem;
  }}
  .stat-card {{
    background: #1e293b;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid #334155;
    transition: transform 0.2s;
  }}
  .stat-card:hover {{ transform: translateY(-2px); }}
  .stat-card .number {{
    font-size: 2.5rem;
    font-weight: 700;
    display: block;
    margin-bottom: 0.25rem;
  }}
  .stat-card .label {{ color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  .section-title {{
    font-size: 1.3rem;
    font-weight: 600;
    margin: 2rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e293b;
    color: #f1f5f9;
  }}
  .flag-summary {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 2rem;
  }}
  .flag-summary-item {{
    background: #1e293b;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    border: 1px solid #334155;
  }}
  .flag-summary-item strong {{ color: #f1f5f9; }}
  .case-card {{
    background: #1e293b;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid #334155;
    transition: all 0.2s;
  }}
  .case-card:hover {{ border-color: #475569; box-shadow: 0 4px 24px rgba(0,0,0,0.3); }}
  .case-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    gap: 0.5rem;
  }}
  .case-id {{
    font-size: 1.1rem;
    font-weight: 600;
    color: #f1f5f9;
    font-family: 'Courier New', monospace;
  }}
  .decision-badge {{
    padding: 0.35rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #fff;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .case-meta {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.5rem;
    margin-bottom: 1rem;
    font-size: 0.85rem;
    color: #94a3b8;
  }}
  .case-meta span strong {{ color: #cbd5e1; }}
  .case-reason {{
    background: #0f172a;
    border-radius: 8px;
    padding: 1rem;
    font-size: 0.9rem;
    line-height: 1.7;
    margin-bottom: 0.75rem;
    border-left: 3px solid #475569;
  }}
  .case-flags {{ margin-top: 0.75rem; }}
  .flag-badge {{
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.75rem;
    color: #fff;
    margin-right: 0.3rem;
    margin-bottom: 0.3rem;
    font-weight: 500;
  }}
  .conf-bar {{
    width: 120px;
    height: 8px;
    background: #334155;
    border-radius: 4px;
    overflow: hidden;
    display: inline-block;
    vertical-align: middle;
    margin-right: 0.5rem;
  }}
  .conf-fill {{ height: 100%; border-radius: 4px; transition: width 0.5s ease; }}
  .conf-label {{ font-size: 0.8rem; color: #94a3b8; }}
  .age-tag {{ font-size: 0.8rem; font-weight: 600; }}
  .evidence-ids {{ font-family: 'Courier New', monospace; color: #38bdf8; font-size: 0.85rem; }}
  footer {{
    text-align: center;
    padding: 2rem 0;
    color: #475569;
    font-size: 0.8rem;
    border-top: 1px solid #1e293b;
    margin-top: 2rem;
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>⚡ Chargeback Audit Trail</h1>
    <p>AI Risk Manager — Automated Evidence Review &amp; Decision Report</p>
    <p style="margin-top:0.5rem;color:#64748b">Generated {date.today().isoformat()} · {total} cases analyzed</p>
  </header>

  <div class="dashboard">
    <div class="stat-card">
      <span class="number" style="color:#38bdf8">{total}</span>
      <span class="label">Total Cases</span>
    </div>
    <div class="stat-card">
      <span class="number" style="color:#10b981">{decision_counts.get('contest', 0)}</span>
      <span class="label">Contest</span>
    </div>
    <div class="stat-card">
      <span class="number" style="color:#ef4444">{decision_counts.get('accept_liability', 0)}</span>
      <span class="label">Accept Liability</span>
    </div>
    <div class="stat-card">
      <span class="number" style="color:#f59e0b">{decision_counts.get('manual_review', 0)}</span>
      <span class="label">Manual Review</span>
    </div>
    <div class="stat-card">
      <span class="number" style="color:#c084fc">{avg_confidence:.0%}</span>
      <span class="label">Avg Confidence</span>
    </div>
  </div>
"""

    if flag_counts:
        html_content += '  <h2 class="section-title">🚩 Risk Signal Summary</h2>\n  <div class="flag-summary">\n'
        for f_name, f_count in sorted(flag_counts.items(), key=lambda x: -x[1]):
            color = FLAG_COLORS.get(f_name, "#374151")
            html_content += f'    <div class="flag-summary-item"><span class="flag-badge" style="background:{color}">{html.escape(f_name.replace("_", " "))}</span> <strong>{f_count}</strong> cases</div>\n'
        html_content += '  </div>\n'

    html_content += '  <h2 class="section-title">📋 Case-by-Case Audit Trail</h2>\n'

    for pred in predictions:
        cid = pred["case_id"]
        case = case_map.get(cid, {})
        decision = pred.get("decision", "unknown")
        bg, _, icon = DECISION_COLORS.get(decision, ("#475569", "#1e293b", "?"))

        txn_date = case.get("transaction_date", "n/a")
        age_html = dispute_age_indicator(txn_date)

        html_content += f"""
  <div class="case-card">
    <div class="case-header">
      <span class="case-id">{html.escape(cid)}</span>
      <span class="decision-badge" style="background:{bg}">{icon} {html.escape(decision.replace('_', ' '))}</span>
    </div>
    <div class="case-meta">
      <span><strong>Amount:</strong> ₹{html.escape(case.get('amount', '?'))}</span>
      <span><strong>Reason Code:</strong> {html.escape(case.get('reason_code', '?'))}</span>
      <span><strong>Payment:</strong> {html.escape(case.get('payment_method', '?'))}</span>
      <span><strong>Txn Date:</strong> {html.escape(txn_date)} {age_html}</span>
      <span><strong>Merchant:</strong> {html.escape(case.get('merchant_id', '?'))}</span>
      <span><strong>Confidence:</strong> {confidence_bar(pred.get('confidence', 0))}</span>
    </div>
    <div class="case-reason">{html.escape(pred.get('reason', 'No reason provided.'))}</div>
    <div class="case-flags">
      <strong style="font-size:0.85rem;color:#94a3b8">Risk Flags: </strong>{flag_badges(pred.get('risk_flags', 'none'))}
    </div>
    <div style="margin-top:0.5rem">
      <strong style="font-size:0.85rem;color:#94a3b8">Cited Evidence: </strong>
      <span class="evidence-ids">{html.escape(pred.get('cited_evidence_ids', 'none'))}</span>
      <strong style="font-size:0.85rem;color:#94a3b8;margin-left:1rem">Sufficiency: </strong>
      <span style="font-size:0.85rem">{html.escape(pred.get('evidence_sufficiency', '?'))}</span>
    </div>
  </div>
"""

    html_content += f"""
  <footer>
    RiskManager &middot; AI Risk Manager &middot; Track 02 &middot; Chargeback Evidence Responder<br>
    Every decision explainable, bounded, and gated. This is the audit trail.
  </footer>
</div>
</body>
</html>"""

    report_path.write_text(html_content, encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="Generate HTML audit trail report")
    parser.add_argument("--cases", default="dataset/dev/cases.csv",
                        help="Path to cases CSV (resolved against repo root)")
    parser.add_argument("--output", default="dataset/dev/output.csv",
                        help="Path to pipeline output CSV (resolved against repo root)")
    args = parser.parse_args()

    cases_path = REPO_ROOT / args.cases
    output_path = REPO_ROOT / args.output

    cases = load_csv(cases_path)
    predictions = load_csv(output_path)

    report_path = generate_report(cases, predictions, output_path)
    print(f"[OK] Audit trail report generated: {report_path}")
    print(f"  {len(predictions)} cases, open in a browser to view.")


if __name__ == "__main__":
    main()
