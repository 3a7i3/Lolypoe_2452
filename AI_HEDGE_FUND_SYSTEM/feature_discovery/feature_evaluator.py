import pandas as pd

class FeatureEvaluator:
    def evaluate(self, feature, returns):
        aligned = pd.concat([feature, returns], axis=1).dropna()
        score = aligned.corr().iloc[0,1]
        return score
