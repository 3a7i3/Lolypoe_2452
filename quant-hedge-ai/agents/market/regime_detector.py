from __future__ import annotations


class RegimeDetector:
    def detect(self, momentum: float, volatility: float) -> str:
        if volatility > 0.03:
            return "high_volatility"
        if momentum > 0.01:
            return "bull"
        if momentum < -0.01:
            return "bear"
        return "sideways"
