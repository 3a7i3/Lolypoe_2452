# Project Guidelines

## Scope And Priorities

This workspace contains multiple independent trading systems. Treat each top-level project as a separate codebase unless explicitly asked to integrate across them.

Current priority order:
1. quant-hedge-ai (V9.1 autonomous quant lab)
2. crypto_quant_v16 (V16/V26/V30 dashboard + execution stack)
3. quant-ai-system (Docker-based stack)
4. Legacy folders (bot-v3, quant-bot-v3-pro, quant-hedge-bot, quant-trading-system) are reference-only unless the user explicitly requests changes there.

## Architecture Boundaries

- quant-hedge-ai:
  - Main entrypoint: main_v91.py
  - Agent-oriented structure under agents/, plus engine/, dashboard/, databases/.
- crypto_quant_v16:
  - Main entrypoint: main_v16.py
  - UI entrypoint: ui/quant_dashboard.py and versioned dashboard variants.
  - Core layers: core/, ai/, quant/, ui/.
- quant-ai-system:
  - Containerized architecture with docker-compose and infrastructure services.

Do not move files or merge patterns across systems without user approval.

## Build, Run, And Health Commands

Use PowerShell on Windows and run from the indicated directory.

V9.1 quick run (preferred default):
- From workspace root:
  - .\.venv\Scripts\Activate.ps1
  - cd quant-hedge-ai
  - $env:V9_MAX_CYCLES="1"; python main_v91.py

V16 dashboard:
- cd crypto_quant_v16
- launch_v16_dashboard.bat
- Fallback: panel serve ui\quant_dashboard.py --port 5011 --show

V16 autonomous loop:
- cd crypto_quant_v16
- python main_v16.py

V30 health checks (crypto_quant_v16):
- healthcheck_v30.bat
- or healthcheck_v30.ps1

Workspace orchestration:
- Start: launch_all.bat or launch_all.ps1 -Visible -LoadEnv
- Stop: stop_all.bat

Testing examples:
- cd crypto_quant_v16
- python test_v30_profile.py
- python test_v30_multi_exchange.py
- python test_v30_profile_persistence.py
- python test_v30_smart_chart.py

## Code Conventions

- Follow existing style in the touched file; do not reformat unrelated code.
- Prefer pathlib over os.path in Python when introducing new path logic.
- Preserve versioned naming patterns (v13, v16, v26, v30, v91) and avoid broad renames.
- Keep tests close to the target system and follow existing test naming in that area.
- Prefer minimal, targeted patches over large refactors.

## Environment And Runtime Pitfalls

- VS Code terminals persist working directory; avoid repeated nested cd commands that duplicate paths.
- On this Windows setup, one launched Python task can appear as parent/child python.exe processes; verify before killing both.
- V9.1 may need PYTHONPATH set to project root if imports fail in some shells.
- Port collisions are common (5010/5011/5013/5026, and 8502 in quant-ai-system). Check listeners before changing runtime code.
- Some health checks depend on external network/exchange response and may warn on timeout; treat these as connectivity warnings unless the user asks for strict failure.
- In V26/V30 live data modes, mock fallback labels are meaningful and can intentionally force HOLD behavior in strict live mode.

## Safe Defaults For Agent Changes

- Prefer paper/simulated trading settings unless the user explicitly asks for live-trading changes.
- Do not introduce real API keys, secrets, or hardcoded credentials.
- For behavior changes in trading/risk logic, add or update at least one focused test in the same system.

## Pointers

- Root orientation: README.md and QUICK_START_V91.md
- V16 details: crypto_quant_v16/README.md and crypto_quant_v16/QUICK_START.md
- V9.1 configuration and validation: CONFIG_REFERENCE_V91.md and VALIDATION_CHECKLIST.md
