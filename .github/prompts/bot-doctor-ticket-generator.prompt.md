---
name: bot-doctor-ticket-generator
description: "Use when you need implementation tickets (epics/stories/tasks) for Bot Doctor, Telegram alerts, consensus validation, and risk automation features."
argument-hint: "Colle le scope + systèmes cibles + langue=fr|en|bilingue (optionnel)"
agent: "agent"
---

Generate engineering tickets for Bot Doctor platform enhancements.

Language policy:
- Default output language: French.
- Optional switch: `lang=fr`, `lang=en`, or `lang=bilingue`.

Task focus:
- One task only: convert requirements into delivery-ready tickets.

Output format:
## 1) Epics
- 4 to 8 epics with objective and business value.

## 2) User Stories
- For each epic, provide stories in this format:
  - Title
  - As a / I want / So that
  - Acceptance criteria (testable)
  - Dependencies
  - Priority (P0/P1/P2)

## 3) Technical Tasks
- For each story:
  - Implementation tasks
  - Files/services likely impacted
  - Definition of done

## 4) QA Tasks
- Unit/integration/simulation checks.
- Negative tests for Bot Doctor false positives/negatives.

## 5) Release Slices
- Group tickets into 2-week delivery slices.
- Include risk level and rollback note per slice.

Constraints:
- Keep ticket wording concise and testable.
- Prefer deterministic requirements over vague goals.
- No secrets or production credentials.
- Default to simulation-safe behavior unless live mode is explicitly requested.
- Respect selected language policy for the full output.
