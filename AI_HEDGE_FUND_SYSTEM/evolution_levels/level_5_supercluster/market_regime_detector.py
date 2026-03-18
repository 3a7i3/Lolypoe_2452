# Niveau 5 — MarketRegimeDetector
import numpy as np

class MarketRegimeDetector:
    def detect(self, df):
        volatility = df["close"].pct_change().std()
        if volatility > 0.04:
            return "high_volatility"
        trend = df["close"].iloc[-1] - df["close"].iloc[-50]
        if trend > 0:
            return "bull"
        return "bear"
