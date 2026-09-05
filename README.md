<div align="center">

  # RiskManager

  ### Intelligent Chargeback Evidence Evaluation

  *Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager*

  ![Track 02](https://img.shields.io/badge/TRACK_02-AI_RISK_MANAGER-2f6fed?style=for-the-badge)
  ![Postured for Defense](https://img.shields.io/badge/POSTURE-DEFENSE--ONLY-2f6fed?style=for-the-badge)
  ![Tests Passing](https://img.shields.io/badge/TESTS-35_PASSING-2ea44f?style=for-the-badge)

</div>

---

RiskManager is an autonomous AI agent designed to evaluate chargeback disputes. By analyzing transaction metadata, reason codes, merchant evidence, and free-text narratives, the system decides whether a chargeback should be contested, accepted, or routed for human review. It also includes an interactive HTML dashboard for auditing and visualizing the system's decisions, along with advanced deterministic signals like `temporal_anomaly` to detect edge cases.

## Core Capabilities
- **Automated Decision Engine:** Leverages the Groq API (using the Qwen model) to read merchant narratives and classify evidence.
- **Deterministic Risk Signals:** Employs pure code to flag objective risks like `temporal_anomaly` (disputes older than 120 days), `amount_anomaly`, and `merchant_repeat_pattern`.
- **Interactive Web Dashboard:** A real-time Flask-powered web UI (`app.py`) with animated stats, filterable case list, expandable detail panels, and risk signal visualization — built for live demos and auditor review.
- **Static Audit Report:** Also generates a self-contained HTML report (`report.py`) that can be shared offline.
- **Adversarial Robustness:** Designed with a defense-only posture to withstand prompt injections in the merchant narrative.

## System Architecture

RiskManager strictly separates objective facts from subjective evaluation. Arithmetic, date calculations, and strict rule-matching are handled by standard Python logic. The LLM is exclusively tasked with tasks requiring human-like judgment, such as interpreting the context of a merchant's narrative.

- **`code/main.py`**: The core execution loop. It forces the LLM to provide a structured answer within two iterations.
- **`code/app.py`**: Flask web server powering the interactive dashboard at `http://127.0.0.1:5000`.
- **`code/risk_signals.py`**: Deterministic evaluators. Calculates factors like `temporal_anomaly` without utilizing token limits.
- **`code/report.py`**: Compiles execution results into a responsive, dark-mode HTML interface (`audit_report.html`).
- **`code/llm_cache.py`**: A local disk cache that hashes requests to avoid redundant API calls and conserve Groq quotas.

## Getting Started

### Prerequisites and Setup

Navigate to the source directory and create a virtual environment:

```bash
cd code
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r ../requirements.txt
```

Set up your API keys:
```bash
cp ../.env.example ../.env
```
Add your `GROQ_API_KEY` to the `.env` file. (Note: The `.gitignore` has been thoroughly configured to prevent accidental credential leaks).

### Running the System

1. **Test the pipeline (no API required):**
   ```bash
   python -m pytest ../tests/ -v
   ```

2. **Execute the evaluation engine:**
   ```bash
   python main.py --input dataset/demo/cases.csv --output dataset/demo/output.csv
   ```

3. **Launch the Interactive Web Dashboard:**
   ```bash
   python app.py
   ```
   Open **http://127.0.0.1:5000** in your browser. The dashboard features:
   - Animated stat counters for total cases, decisions, and confidence
   - Risk signal summary bar with color-coded badges
   - Filter tabs to view Contest / Accept Liability / Manual Review cases
   - Expandable case cards with full AI reasoning, evidence, merchant narrative, and risk flags
   - Dataset switcher to toggle between demo and dev datasets

4. **Generate the static HTML Report (optional):**
   ```bash
   python report.py --cases dataset/demo/cases.csv --output dataset/demo/output.csv
   ```
   *Open `dataset/demo/audit_report.html` in any web browser to view the results.*

## Evaluation and Metrics

The system has been comprehensively evaluated against a synthetic dataset. It maintains strict standards for zero false positives on automated decisions. If a case exhibits significant risk signals, the system defaults to routing it to `manual_review` rather than risking an incorrect automated action. 

The integration of the web dashboard and `temporal_anomaly` flag directly addresses the need for interpretable, explainable AI in financial risk management.

## Security Posture
- **Least Privilege:** Tool execution strictly utilizes internal data references; it ignores user-provided or LLM-hallucinated case IDs.
- **No Real PII:** All datasets are entirely synthetic.
- **Secure Key Management:** Hardcoded keys are banned, and pre-commit hooks enforce safety.

