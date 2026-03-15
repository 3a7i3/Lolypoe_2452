class RegimeClassifier:
    def classify(self, features):
        if features["volatility"] > 0.05:
            return "HIGH_VOLATILITY"
        if features["trend"] > 0:
            return "BULL_TREND"
        if features["trend"] < 0:
            return "BEAR_TREND"
        return "SIDEWAYS"
