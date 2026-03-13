# V9 Autonomous Quant Hedge Fund System

This module adds a V9 multi-agent quant lab architecture with autonomous research cycles.

## Run

```powershell
cd quant-hedge-ai
python main_system.py
```

Optional environment variables:

- `V9_MAX_CYCLES` default `3` (`0` means infinite loop)
- `V9_POPULATION` default `300`
- `V9_SLEEP_SECONDS` default `2`

## What it does each cycle

1. Scan market snapshots
2. Generate and evolve strategies (genetic optimizer)
3. Backtest strategy population
4. Rank by Sharpe and drawdown
5. Store best strategies in local database
6. Retrain model score proxy
7. Execute paper-trading orders
8. Print monitoring report
