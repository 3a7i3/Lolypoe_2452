import pandas as pd

class FeatureEngine:
    def compute(self, df):
        df["momentum"] = df["close"].pct_change()
        df["volatility"] = df["close"].rolling(20).std()
        df["mean"] = df["close"].rolling(20).mean()
        return df
