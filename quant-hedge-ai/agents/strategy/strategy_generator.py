from __future__ import annotations

import random

INDICATORS = ["RSI", "MACD", "EMA", "BOLLINGER", "VWAP", "ATR"]
TIMEFRAMES = ["5m", "15m", "1h", "4h"]


class StrategyGenerator:
    def generate(self) -> dict:
        return {
            "entry_indicator": random.choice(INDICATORS),
            "exit_indicator": random.choice(INDICATORS),
            "period": random.randint(5, 80),
            "threshold": round(random.uniform(0.2, 2.5), 3),
            "timeframe": random.choice(TIMEFRAMES),
        }

    def generate_population(self, n: int) -> list[dict]:
        return [self.generate() for _ in range(max(1, n))]
