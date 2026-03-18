class FeatureAgent:
    def build_features(self, df):
        print("[FeatureAgent] Building features...")
        # Dummy features (pas de pandas)
        df["momentum"] = 0.1
        df["volatility"] = 0.2
        return df
