"""Advanced regime detection with market regime classification."""
from __future__ import annotations


class AdvancedRegimeDetector:
    def __init__(self) -> None:
        self.regimes = ["bull_trend", "bear_trend", "sideways", "high_volatility_regime", "flash_crash"]

    def classify(self, features: dict, recent_prices: list[float] | None = None) -> str:
        momentum = float(features.get("momentum", 0.0))
        vol = float(features.get("realized_volatility", 0.0))
        trend = float(features.get("trend_strength", 0.5))

        if vol > 0.15:
            return "high_volatility_regime"

        if momentum > 0.03 and trend > 0.7:
            return "bull_trend"

        if momentum < -0.03 and trend < 0.3:
            return "bear_trend"

        if abs(momentum) < 0.01 and vol < 0.05:
            return "sideways"

        if vol > 0.2:
            return "flash_crash"

        return "sideways"

    def suggest_strategy_type(self, regime: str) -> str:
        """Suggest strategy class for detected regime."""
        if regime == "bull_trend":
            return "momentum_following"
        if regime == "bear_trend":
            return "short_strategies"
        if regime == "sideways":
            return "mean_reversion"
        if regime in ["high_volatility_regime", "flash_crash"]:
            return "volatility_harvesting"
        return "neutral"
