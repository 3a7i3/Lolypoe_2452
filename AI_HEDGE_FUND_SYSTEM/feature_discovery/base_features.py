import pandas as pd

class BaseFeatures:
    def compute(self, df):
        features = pd.DataFrame()
        features["returns"] = df["close"].pct_change()
        features["momentum_10"] = df["close"].pct_change(10)
        features["momentum_50"] = df["close"].pct_change(50)
        features["volatility_20"] = features["returns"].rolling(20).std()
        features["mean_50"] = df["close"].rolling(50).mean()
        return features
