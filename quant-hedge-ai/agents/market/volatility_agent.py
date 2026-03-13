from __future__ import annotations

from statistics import mean


class VolatilityDetector:
    def detect(self, closes: list[float]) -> float:
        if len(closes) < 2:
            return 0.0
        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes)) if closes[i - 1] != 0]
        if not returns:
            return 0.0
        avg = mean(returns)
        var = mean((r - avg) ** 2 for r in returns)
        return var ** 0.5
