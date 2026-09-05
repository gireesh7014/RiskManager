# System Architecture: RiskManager

This document outlines the technical design of RiskManager, focusing on how components interact to safely process chargeback evidence without hallucination or vulnerability to prompt injection.

## Overview of Components

| Module | Location | Purpose |
|---|---|---|
| **Core Engine** | `code/main.py` | Orchestrates the multi-round LLM agent loop and finalizes decisions. |
| **Deterministic Rules** | `code/risk_signals.py` | Calculates hard constraints such as `temporal_anomaly`, `amount_anomaly`, and `merchant_repeat_pattern`. |
| **Dashboard Generator**| `code/report.py` | Transforms CSV outputs into a rich, interactive HTML interface for auditors. |
| **Caching Layer** | `code/llm_cache.py` | Hashes prompts and stores responses to save API tokens and speed up iteration. |
| **Test Suite** | `tests/` | Contains 35 passing tests, including adversarial defense checks and logic verification. |

## Data Flow

1. **Context Assembly:** The system loads the case data and calculates deterministic flags. For instance, if the dispute is older than 120 days, the `temporal_anomaly` flag is immediately set.
2. **LLM Evaluation:** The Groq API (using the Qwen model) is queried. It can request additional data tools or immediately classify the case.
3. **Tool Execution Guardrails:** If the LLM requests evidence, the system ignores the LLM's arguments and injects the actual context for the current case.
4. **Overrides:** Before outputting, the system forcefully applies the deterministic flags (e.g., if a temporal anomaly exists, it remains flagged, regardless of LLM sentiment).
5. **Report Generation:** `report.py` ingests the final outputs and renders a responsive `audit_report.html` file.

## Why Separate Logic from LLMs?

We only use the LLM where strict code fails: reading free-text narratives for context. We never ask the LLM to do math, calculate dates, or match enum categories. This hybrid architecture ensures that the system remains both highly capable and rigorously predictable.
