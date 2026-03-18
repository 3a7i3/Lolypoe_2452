# Niveau 5 — FeatureDiscoveryEngine
import numpy as np

class FeatureDiscoveryEngine:
    def generate(self, df):
        # Exemples de features composites
        if "rsi" in df and "volume" in df:
            df["feature_1"] = df["rsi"] * df["volume"]
        if "momentum" in df and "volatility" in df:
            df["feature_2"] = df["momentum"] * df["volatility"]
        if "volume" in df and "volatility" in df:
            df["feature_3"] = df["volume"] / (df["volatility"] + 1e-8)
        return df
