from __future__ import annotations

from statistics import mean


class PerformanceMonitor:
    def summarize(self, experiment_results: list[dict]) -> dict:
        if not experiment_results:
            return {"avg_sharpe": 0.0, "avg_drawdown": 0.0, "avg_pnl": 0.0}

        return {
            "avg_sharpe": round(mean(float(r.get("sharpe", 0.0)) for r in experiment_results), 4),
            "avg_drawdown": round(mean(float(r.get("drawdown", 0.0)) for r in experiment_results), 4),
            "avg_pnl": round(mean(float(r.get("pnl", 0.0)) for r in experiment_results), 4),
        }
