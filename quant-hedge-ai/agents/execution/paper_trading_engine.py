from __future__ import annotations


class PaperTradingEngine:
    def __init__(self, initial_balance: float = 100_000.0) -> None:
        self.balance = initial_balance
        self.positions: dict[str, float] = {}

    def execute(self, order: dict, mark_price: float) -> dict:
        symbol = order["symbol"]
        action = order["action"]
        size = float(order["size"])
        notional = size * mark_price

        if action == "BUY" and self.balance >= notional:
            self.balance -= notional
            self.positions[symbol] = self.positions.get(symbol, 0.0) + size
        elif action == "SELL":
            current = self.positions.get(symbol, 0.0)
            sold = min(current, size)
            self.positions[symbol] = current - sold
            self.balance += sold * mark_price

        return {
            "balance": round(self.balance, 2),
            "positions": {k: round(v, 6) for k, v in self.positions.items() if v > 0},
        }
