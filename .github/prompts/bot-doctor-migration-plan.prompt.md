---
name: bot-doctor-migration-plan
description: "Use when you need a step-by-step migration plan to introduce Bot Doctor supervision into an existing trading stack with minimal regression risk."
argument-hint: "Fournis architecture actuelle + contraintes + langue=fr|en|bilingue (optionnel)"
agent: "agent"
---

Create a migration plan to introduce Bot Doctor supervision into an existing trading platform.

Language policy:
- Default output language: French.
- Optional switch: `lang=fr`, `lang=en`, or `lang=bilingue`.

Task focus:
- One task only: migration design and execution sequence.

Required output:
## 1) Current vs Target State
- Brief baseline architecture.
- Target architecture with Bot Doctor checkpoints.

## 2) Migration Strategy
- Choose approach: strangler, parallel run, or in-place refactor.
- Explain why this approach fits constraints.

## 3) Incremental Phases
- Phase 1, 2, 3 with:
  - Scope
  - Dependencies
  - Rollback path
  - Exit criteria

## 4) Compatibility Matrix
- Interfaces/events to keep backward compatible.
- Required adapters and deprecation timeline.

## 5) Risk Controls
- Regression risks and mitigations.
- Simulation-first rollout gates.
- Live activation checklist (optional).

## 6) Validation Plan
- Test plan per phase.
- Shadow-mode and canary strategy.
- Success metrics and stop conditions.

Constraints:
- Be concrete and implementation-ready.
- Do not include secrets.
- Default to paper/sim mode unless explicitly requested otherwise.
- Respect selected language policy for the full output.
