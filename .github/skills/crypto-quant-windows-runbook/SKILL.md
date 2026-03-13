---
name: crypto-quant-windows-runbook
description: 'Run and validate crypto quant systems on Windows. Use when launching dashboard or autonomous loops, performing preflight checks, verifying runtime health, and troubleshooting port/import/performance issues for crypto_quant_v16 and quant-hedge-ai (V9.1).'
argument-hint: '[target: v16|v91] [mode: dashboard|loop|smoke-test]'
user-invocable: true
disable-model-invocation: false
---

# Crypto Quant Windows Runbook

## What This Skill Produces

- A repeatable Windows run sequence for `crypto_quant_v16` and `quant-hedge-ai`.
- A validated result with clear pass/fail checks.
- Fast troubleshooting branches for the most common startup failures.

## When To Use

- You want to start the V16 dashboard quickly.
- You want to run one autonomous loop and confirm system health.
- You need a smoke test before deeper development.
- You see startup issues (port conflict, import errors, slow execution) and need a deterministic triage path.

## Inputs

- `target`: `v16` or `v91`
- `mode`: `dashboard`, `loop`, or `smoke-test`
- Optional constraints: expected runtime budget, preferred port, minimal test settings

## Procedure

1. Preflight environment.
2. Choose target and run path.
3. Execute launch command.
4. Validate completion criteria.
5. If any check fails, follow troubleshooting branches.
6. Report status and next action.

## Step 1: Preflight Environment

Run these checks first:

```powershell
Get-ChildItem -Path env: | Where-Object {$_.Name -eq "VIRTUAL_ENV"}
python --version
pip list | Select-Object -First 20
```

Pass criteria:

- Virtual environment is active.
- Python is 3.11+.
- Core packages are installed (for example `numpy`, `pandas`, `plotly`, `panel`).

If preflight fails:

- Activate env: `.\.venv\Scripts\Activate.ps1`
- Reinstall deps in target project: `pip install -r requirements.txt --force-reinstall`

## Step 2: Choose Target And Mode

Decision table:

- `target=v16`, `mode=dashboard`: interactive UI for monitoring and exploration.
- `target=v16`, `mode=loop`: run orchestrated trading cycle output in terminal.
- `target=v91`, `mode=smoke-test`: fastest confidence check with constrained cycle settings.
- `target=v91`, `mode=loop`: standard autonomous quant run.

## Step 3: Launch Commands

### V16 Dashboard

```powershell
cd crypto_quant_v16
launch_v16_dashboard.bat
```

Fallback:

```powershell
panel serve ui/quant_dashboard.py --port 5011 --show
```

### V16 Loop

```powershell
cd crypto_quant_v16
python main_v16.py
```

### V91 Smoke Test

```powershell
cd quant-hedge-ai
$env:V9_MAX_CYCLES = "1"
$env:V9_POPULATION = "10"
$env:V9_GENERATIONS = "1"
python main_v91.py
```

### V91 Standard Loop

```powershell
cd quant-hedge-ai
python main_v91.py
```

## Step 4: Completion Checks

For `v16` loop, confirm:

- Cycle phases are printed in order: scan, strategy, optimize, execute, risk validation.
- No exceptions in terminal output.

For `v16` dashboard, confirm:

- Panel app opens and route loads.
- Dashboard tabs are visible and responsive.

For `v91`, confirm:

- Control center sections render (market regime, whale radar, best strategy, scoreboard, portfolio, execution decision, health).
- Run completes within expected smoke-test budget (typically under 30 seconds for constrained settings).
- No import/type/runtime exceptions.

## Step 5: Troubleshooting Branches

### Branch A: Port Conflict

```powershell
netstat -an | findstr :5011
```

Resolution:

- Use another port: `panel serve ui/quant_dashboard.py --port 5012`

### Branch B: Import Or Dependency Errors

```powershell
pip install -r requirements.txt --force-reinstall
python -m py_compile main_v16.py
```

For V91 main validation:

```powershell
python -m py_compile main_v91.py
python -c "import main_v91"
```

### Branch C: Slow Runtime

Reduce workload parameters before rerun:

- Fewer symbols.
- Smaller strategy population.
- Single-cycle smoke test.

## Step 6: Output Contract

At the end of each run, output:

- Selected target/mode and command used.
- Pass/fail for each validation check.
- If failed, which branch was used and result.
- Recommended next action (rerun, adjust config, or proceed to extended test).

## Quality Gate

Mark task complete only when all are true:

- Environment checks passed.
- Launch command executed successfully.
- Required runtime sections/metrics appeared.
- No unresolved errors remain.