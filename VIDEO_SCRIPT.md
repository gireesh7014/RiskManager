# 5-Minute Demo Script: RiskManager

This script is designed for a screen-recorded demonstration of the RiskManager project. 

---

## 0:00 - 1:00: Introduction & The Problem
*Visual: Show the RiskManager GitHub repository and the README.*

"Hello, this is RiskManager. In the payment ecosystem, chargebacks are a massive source of operational loss. When a chargeback occurs, someone has to read the merchant's evidence and decide whether to fight the chargeback or accept the loss.

RiskManager is an AI agent that automates this process. It reads the evidence, analyzes the merchant's narrative, cross-references historical data, and makes a financial decision—explaining exactly why it made it."

## 1:00 - 2:00: The Architecture & Deterministic Rules
*Visual: Open `code/risk_signals.py` and highlight the `temporal_anomaly` logic.*

"What makes this system robust is our hybrid approach. We don't just blindly trust the LLM. Objective facts are computed in code. For example, I recently added a `temporal_anomaly` risk signal. If a dispute is older than 120 days, Python detects it instantly. The LLM handles the subjective reading of the narrative, but it cannot override these hard, deterministic facts."

## 2:00 - 3:00: Running the Pipeline & Security
*Visual: Terminal window. Run the test suite (`pytest`), then run `main.py` on the demo dataset.*

"Security is critical. The merchant's narrative is treated as untrusted input. Our adversarial testing ensures that merchants can't use prompt injection to trick the AI into approving a bad case. Also, when the LLM calls internal tools, the system sandboxes the request, ensuring the AI can only access data for the current active case.

Let's run the system on our demo dataset. Thanks to our local disk caching, it runs incredibly fast and saves API tokens."

## 3:00 - 4:30: The Visual Dashboard
*Visual: Run `report.py` and then open `audit_report.html` in the browser.*

"A decision isn't useful if a human auditor can't understand it. So, we built a dynamic HTML dashboard. As you can see, the report visualizes every single case. We have confidence progress bars, color-coded decision tags, and badges for our risk flags—including the new Temporal Anomaly flag. This allows a human review team to quickly verify the AI's logic."

## 4:30 - 5:00: Conclusion
*Visual: Show the passing test suite again or the top of the README.*

"In conclusion, RiskManager provides a secure, explainable, and highly accurate solution for chargeback disputes. It combines the reasoning power of the Groq LLM with strict deterministic guardrails to ensure financial safety. Thank you."
