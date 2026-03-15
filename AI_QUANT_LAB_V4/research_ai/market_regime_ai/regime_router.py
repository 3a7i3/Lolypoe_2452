class RegimeRouter:
    def __init__(self):
        self.mapping = {
            "BULL_TREND": ["momentum_strategy"],
            "BEAR_TREND": ["short_trend_strategy"],
            "SIDEWAYS": ["mean_reversion"],
            "HIGH_VOLATILITY": ["volatility_breakout"]
        }
    def strategies_for(self, regime):
        return self.mapping.get(regime, [])
