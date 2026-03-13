from __future__ import annotations

import random
from statistics import mean


class BacktestLab:
    """Runs synthetic backtests and returns common quant metrics."""

    def run_backtest(self, strategy: dict, data: list[dict]) -> dict:
        seed = abs(hash(str(strategy))) % (10**6)
        random.seed(seed)
        returns = [random.uniform(-0.02, 0.03) for _ in range(max(20, len(data) * 10))]
        avg = mean(returns)
        variance = mean((r - avg) ** 2 for r in returns)
        vol = variance ** 0.5 if variance > 0 else 1e-9
        sharpe = (avg / vol) * (252**0.5)

        equity = 1.0
        peak = 1.0
        max_dd = 0.0
        wins = 0
        for r in returns:
            equity *= 1 + r
            peak = max(peak, equity)
            dd = (peak - equity) / peak if peak else 0.0
            max_dd = max(max_dd, dd)
            if r > 0:
                wins += 1

        return {
            "strategy": strategy,
            "pnl": round((equity - 1.0) * 100, 4),
            "sharpe": round(sharpe, 4),
            "drawdown": round(max_dd, 4),
            "win_rate": round(wins / len(returns), 4),
        }
