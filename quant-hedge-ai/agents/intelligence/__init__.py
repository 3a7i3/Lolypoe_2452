"""Intelligence layer for advanced feature engineering and anomaly detection."""
from __future__ import annotations

from statistics import mean, stdev


class FeatureEngineer:
    """Advanced feature engineering for market micro-structure analysis."""

    def extract_features(self, candles: list[dict]) -> dict:
        """Extract powerful features from OHLCV data."""
        if not candles or len(candles) < 3:
            return self._empty_features()

        closes = [float(c["close"]) for c in candles]
        volumes = [float(c["volume"]) for c in candles]
        highs = [float(c["high"]) for c in candles]
        lows = [float(c["low"]) for c in candles]

        # Price momentum
        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes)) if closes[i - 1] != 0]
        momentum = (closes[-1] - closes[0]) / closes[0] if closes[0] else 0.0

        # Volatility (realized)
        avg_return = mean(returns) if returns else 0.0
        variance = mean((r - avg_return) ** 2 for r in returns) if returns else 0.0
        realized_vol = (variance ** 0.5) if variance > 0 else 0.0

        # Volume analysis
        avg_volume = mean(volumes) if volumes else 0.0
        volume_trend = volumes[-1] / avg_volume if avg_volume > 0 else 1.0

        # Price range (volatility proxy)
        recent_range = (max(highs[-5:]) - min(lows[-5:])) / mean(closes[-5:]) if closes else 0.0

        # Trend strength (HML = High-Minus-Low)
        recent_high = max(highs[-10:]) if len(highs) >= 10 else max(highs)
        recent_low = min(lows[-10:]) if len(lows) >= 10 else min(lows)
        trend_strength = (closes[-1] - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5

        return {
            "momentum": round(momentum, 6),
            "realized_volatility": round(realized_vol, 6),
            "volume_trend": round(volume_trend, 4),
            "price_range_ratio": round(recent_range, 6),
            "trend_strength": round(trend_strength, 4),
            "returns_mean": round(avg_return, 6),
            "returns_std": round(stdev(returns) if returns and len(returns) > 1 else 0.0, 6),
        }

    def _empty_features(self) -> dict:
        return {
            "momentum": 0.0,
            "realized_volatility": 0.0,
            "volume_trend": 1.0,
            "price_range_ratio": 0.0,
            "trend_strength": 0.5,
            "returns_mean": 0.0,
            "returns_std": 0.0,
        }

    def detect_anomalies(self, features: dict) -> list[str]:
        """Detect statistical anomalies that might signal opportunities."""
        anomalies = []

        if abs(features["momentum"]) > 0.05:
            anomalies.append(f"extreme_momentum_{features['momentum']:.4f}")

        if features["realized_volatility"] > 0.1:
            anomalies.append("spike_volatility")

        if features["volume_trend"] > 3.0:
            anomalies.append("volume_explosion")

        if features["trend_strength"] > 0.8 or features["trend_strength"] < 0.2:
            anomalies.append("extreme_trend")

        return anomalies
