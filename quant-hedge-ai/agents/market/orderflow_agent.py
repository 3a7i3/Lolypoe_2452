from __future__ import annotations

import random


class OrderFlowAnalyzer:
    """Estimates synthetic order-flow imbalance."""

    def analyze(self, symbols: list[str]) -> dict[str, float]:
        return {symbol: random.uniform(-1.0, 1.0) for symbol in symbols}
