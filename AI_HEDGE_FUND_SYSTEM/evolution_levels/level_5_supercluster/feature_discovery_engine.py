# Niveau 5 — FeatureDiscoveryEngine
import numpy as np

class FeatureDiscoveryEngine:
    def generate(self, df):
        df["feature_1"] = df["rsi"] * df["volume"]
        df["feature_2"] = df["momentum"] * df["volatility"]
        df["feature_3"] = df["volume"] / (df["volatility"] + 1e-8)
        return df
