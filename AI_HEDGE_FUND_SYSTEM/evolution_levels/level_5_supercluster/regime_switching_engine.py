# Niveau 5 — RegimeSwitchingEngine
import numpy as np

class RegimeSwitchingEngine:
    def detect_regime(self, df):
        trend = df["close"].iloc[-1] - df["close"].iloc[-50]
        volatility = df["close"].pct_change().std()
        if volatility > 0.05:
            return "high_volatility"
        if trend > 0:
            return "bull"
        return "bear"
