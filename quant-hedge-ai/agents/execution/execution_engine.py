from __future__ import annotations


class ExecutionEngine:
    def create_order(self, symbol: str, action: str, size: float) -> dict:
        return {
            "symbol": symbol,
            "action": action,
            "size": round(max(0.0, size), 4),
            "mode": "paper",
        }
