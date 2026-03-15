"""
StrategyGenerator stub for QUANT_CORE
"""
class StrategyGenerator:
    def __init__(self):
        import random
        self.indicators = ["RSI", "EMA", "MACD", "BB", "MOMENTUM"]
        self.rules = ["cross", "trend", "breakout", "mean_revert"]
        self._rng = random.Random(42)

    def generate(self):
        """Génère une stratégie candidate aléatoire."""
        indicator_count = self._rng.choice([2, 3])
        selected_indicators = self._rng.sample(self.indicators, k=indicator_count)
        rule = self._rng.choice(self.rules)
        params = {
            "rsi_period": self._rng.randint(8, 30),
            "ema_fast": self._rng.randint(5, 20),
            "ema_slow": self._rng.randint(25, 90),
            "bb_period": self._rng.randint(12, 40),
            "momentum_period": self._rng.randint(5, 40),
        }
        return {
            "indicators": selected_indicators,
            "rule": rule,
            "params": params,
            "exposure": self._rng.uniform(1000, 100000),
        }
    def generate_rsi_strategy(self, df):
        print("[StrategyGenerator] Generating RSI strategy")
        return df
