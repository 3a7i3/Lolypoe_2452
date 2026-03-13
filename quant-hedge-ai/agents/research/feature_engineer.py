from __future__ import annotations

from statistics import mean


class FeatureEngineer:
    """Builds compact features from market snapshots for model training."""

    def build(self, candles: list[dict]) -> dict:
        closes = [float(c["close"]) for c in candles]
        volumes = [float(c["volume"]) for c in candles]
        if len(closes) < 3:
            return {"momentum": 0.0, "volatility": 0.0, "avg_volume": mean(volumes) if volumes else 0.0}

        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes)) if closes[i - 1] != 0]
        momentum = (closes[-1] - closes[0]) / closes[0] if closes[0] else 0.0
        avg_return = mean(returns) if returns else 0.0
        variance = mean([(r - avg_return) ** 2 for r in returns]) if returns else 0.0
        return {
            "momentum": momentum,
            "volatility": variance ** 0.5,
            "avg_volume": mean(volumes) if volumes else 0.0,
        }
