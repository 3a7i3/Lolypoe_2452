from __future__ import annotations


class LiquidityAnalyzer:
    def filter_symbols(self, candles: list[dict], min_volume: float = 50_000.0) -> list[str]:
        return [c["symbol"] for c in candles if float(c.get("volume", 0.0)) >= min_volume]
