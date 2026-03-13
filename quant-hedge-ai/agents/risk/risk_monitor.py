from __future__ import annotations


class RiskMonitor:
    def __init__(self, max_drawdown: float = 0.2) -> None:
        self.max_drawdown = max_drawdown

    def check(self, result: dict) -> bool:
        return float(result.get("drawdown", 1.0)) <= self.max_drawdown
