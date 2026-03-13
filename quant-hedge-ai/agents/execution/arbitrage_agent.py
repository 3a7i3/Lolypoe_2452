from __future__ import annotations


class ArbitrageAgent:
    def detect(self, price_a: float, price_b: float, threshold: float = 0.01) -> bool:
        if price_a <= 0:
            return False
        spread = abs(price_a - price_b) / price_a
        return spread > threshold
