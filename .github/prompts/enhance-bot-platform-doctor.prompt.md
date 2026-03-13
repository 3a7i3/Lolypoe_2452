---
name: enhance-bot-platform-doctor
description: "Use when you need a detailed implementation plan to add Telegram + Multi-HF + Copy Trading features, with a Bot Doctor supervisor that detects, corrects, and validates AI trading strategies before execution."
argument-hint: "Colle ton scope + contraintes + langue=fr|en|bilingue (optionnel)"
agent: "agent"
---

Create a detailed, implementation-ready specification to enhance an AI trading platform with a Bot Doctor supervisor.

Context defaults for this workspace:
- Primary targets: both crypto_quant_v16 and quant-hedge-ai.
- Multi-HF handling: support both interpretations unless overridden:
  - multi_hedge_funds: allocation and strategy routing across multiple funds/portfolios.
  - multi_huggingface_models: orchestration of multiple HF models for inference/ensemble.
- Language default: French only.
- Language switch: user can set `lang=fr`, `lang=en`, or `lang=bilingue`.
- Trading mode: simulation-first by default; include a clearly separated optional live-trading activation path.

Use this process:
1. Read the user input and normalize it into a structured spec object.
2. Keep the task focused on one objective: platform enhancement with proactive AI strategy correction.
3. Produce a practical roadmap with architecture, APIs, data flows, testing, and rollout steps.
4. Explicitly separate safe default behavior (paper trading/simulation) from live-trading behavior.
5. Flag unknowns as assumptions and provide specific questions to resolve them.
6. Keep system boundaries explicit: do not merge architectures blindly across independent top-level projects.

Default feature set (apply unless user overrides):
- Integrations: Telegram, Multi-HF, Copy Trading
- Features:
  - Auto-ML cross-market strategies
  - User behavioral analysis (Bull/Bear sentiment)
  - Personalized smart alerts
  - Multi-agent interactive dashboard
  - Dynamic auto-risk management
  - Real-time backtesting and stress tests
  - Automatic correction of creator-AI errors by Bot Doctor
- UI improvements:
  - Interactive financial charts
  - Customizable key indicators
  - Bull/Bear iconography
  - Visual and sound Telegram notifications
  - Bot Doctor console for error tracking and corrections
- Automation:
  - Multi-agent consensus before trade validation
  - Automatic PnL optimization
  - Dynamic risk-limit auto-adjustment
  - Bot Doctor supervision and correction loop
- Bot Doctor role:
  - Detect strategy inconsistencies
  - Correct prediction or logic errors
  - Validate and approve strategy pre-execution
  - Provide detailed feedback to improve upstream AI models
  - Escalate alerts via Telegram and dashboard

System mapping requirement:
- For each proposed module, specify placement in:
  - crypto_quant_v16 (ui/core/ai/quant/risk/services)
  - quant-hedge-ai (agents/engine/dashboard/databases)
- If a module should exist in only one system, explain why.

Output format (strict):

## 1) Executive Goal
- One paragraph describing expected business and technical outcomes.
- Language policy:
  - `lang=fr`: output in French only.
  - `lang=en`: output in English only.
  - `lang=bilingue`: output FR first, then EN.

## 2) Target Architecture
- Components list with responsibilities.
- Event flow from signal generation to execution.
- Bot Doctor control loop: detect -> diagnose -> patch -> validate -> approve/reject -> notify.

## 3) Module Plan
- For each module, provide:
  - Purpose
  - Inputs/outputs
  - Key interfaces (function/service/API names)
  - Failure modes and fallback behavior
- Mandatory modules:
  - Strategy Generator
  - Consensus Engine
  - Risk Engine
  - Bot Doctor
  - Alerting Hub (Telegram + dashboard)
  - Backtest/Stress Engine
  - Copy Trading Connector

## 4) Data Contracts
- Define minimal JSON payload examples for:
  - Strategy proposal
  - Doctor diagnosis report
  - Doctor correction patch
  - Approval decision
  - Alert message

## 5) Implementation Backlog
- 3 phases (MVP, Hardening, Scale).
- For each phase provide:
  - User stories
  - Technical tasks
  - Acceptance criteria
  - Priority (P0/P1/P2)

## 6) Risk And Safety
- Trading, model, and operational risks.
- Guardrails for paper mode vs live mode.
- Kill-switch and rollback procedure.

## 7) Test Strategy
- Unit, integration, simulation, and stress tests.
- Bot Doctor regression tests (must include false positive/false negative checks).
- Example test matrix table.

## 8) Observability
- Logs, metrics, traces.
- Required dashboards and alerts.
- SLO/SLA suggestions for latency, error rate, and correction quality.

## 9) Open Questions
- List the top unresolved questions that block implementation.

## 10) Ready-To-Build Deliverables
- Final checklist of code artifacts to create (files/services/jobs).
- Suggested command sequence to implement incrementally.

## 11) Activation Profiles
- Profile A: Simulation/Paper (default, safe).
- Profile B: Live Trading (optional), with explicit preconditions, approvals, and rollback guards.

Quality constraints:
- Be concrete and avoid generic advice.
- Use concise technical language.
- Prefer deterministic workflows over vague autonomous behavior.
- Never include hardcoded secrets or real API keys.
- Default to simulation-safe behavior unless live trading is explicitly requested.
- In bilingual sections, keep terminology consistent across FR/EN.

If the user input is JSON, parse and preserve original intent while improving precision.
If critical fields are missing, continue with explicit assumptions and list them in section 9.
