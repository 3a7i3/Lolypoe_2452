from __future__ import annotations

import random


class MonteCarloSimulator:
    def simulate(self, mean_return: float, volatility: float, steps: int = 120, paths: int = 200) -> dict:
        terminal_values = []
        for _ in range(paths):
            equity = 1.0
            for _ in range(steps):
                shock = random.gauss(mean_return, max(1e-6, volatility))
                # Clamp shocks to avoid impossible <-100% steps and unstable paths.
                shock = max(-0.95, min(0.95, shock))
                equity *= 1 + shock
            terminal_values.append(equity)
        terminal_values.sort()
        n = len(terminal_values)
        return {
            "median_terminal": round(terminal_values[n // 2], 4),
            "p05_terminal": round(terminal_values[max(0, int(0.05 * n) - 1)], 4),
            "p95_terminal": round(terminal_values[min(n - 1, int(0.95 * n))], 4),
        }
