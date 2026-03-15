
import numpy as np

class SignalGenerator:
    def generate(self, features):
        signals = {}
        signals["momentum_signal"] = np.sign(features["momentum_10"])
        signals["trend_signal"] = (features["mean_50"] > features["mean_200"]).astype(int)
        signals["volatility_signal"] = (features["volatility_20"] > features["volatility_20"].median()).astype(int)
        return signals
