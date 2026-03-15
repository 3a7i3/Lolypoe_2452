from regime_features import RegimeFeatures
from regime_classifier import RegimeClassifier

class MarketRegimeDetector:
    def __init__(self):
        self.features = RegimeFeatures()
        self.classifier = RegimeClassifier()
    def detect(self, df):
        f = self.features.compute(df)
        regime = self.classifier.classify(f)
        return regime
