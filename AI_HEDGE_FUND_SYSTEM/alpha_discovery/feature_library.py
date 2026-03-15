
import pandas as pd

class FeatureLibrary:
    def compute_features(self, df):
        features = {}
        returns = df["close"].pct_change()
        features["momentum_10"] = df["close"].pct_change(10)
        features["momentum_50"] = df["close"].pct_change(50)
        features["volatility_20"] = returns.rolling(20).std()
        features["mean_50"] = df["close"].rolling(50).mean()
        features["mean_200"] = df["close"].rolling(200).mean()
        return pd.DataFrame(features)
