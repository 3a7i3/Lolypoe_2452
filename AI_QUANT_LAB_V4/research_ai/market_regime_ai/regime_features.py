import pandas as pd
import numpy as np

class RegimeFeatures:
    def compute(self, df):
        features = {}
        returns = df["close"].pct_change()
        features["volatility"] = returns.rolling(50).std().iloc[-1]
        features["trend"] = (
            df["close"].rolling(50).mean().iloc[-1]
            - df["close"].rolling(200).mean().iloc[-1]
        )
        features["momentum"] = df["close"].pct_change(50).iloc[-1]
        return features
