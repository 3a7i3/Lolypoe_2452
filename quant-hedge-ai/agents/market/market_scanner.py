from __future__ import annotations

import random
from datetime import datetime, timezone


class MarketScanner:
    """Generates market snapshots for supported symbols."""

    def __init__(self, symbols: list[str] | None = None) -> None:
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

    def scan(self) -> dict:
        snapshots = []
        for symbol in self.symbols:
            base = random.uniform(100, 70000)
            close = base * random.uniform(0.995, 1.005)
            snapshots.append(
                {
                    "symbol": symbol,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "open": base,
                    "close": close,
                    "high": max(base, close) * random.uniform(1.0, 1.01),
                    "low": min(base, close) * random.uniform(0.99, 1.0),
                    "volume": random.uniform(1_000, 500_000),
                }
            )
        return {"candles": snapshots}
