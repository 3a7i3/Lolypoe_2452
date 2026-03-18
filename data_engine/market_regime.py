import numpy as np

class MarketRegimeDetector:
    def __init__(self):
        pass

    def detect(self, df):
        returns = df["close"].pct_change()
        volatility = np.std(returns[-50:])
        trend = df["close"].iloc[-1] - df["close"].iloc[-50]
        if volatility > 0.05:
            return "high_volatility"
        if trend > 0:
            return "bull"
        if trend < 0:
            return "bear"
        return "range"
