# Feature Engineering — Niveau 1
class FeatureEngineering:
    def transform(self, data):
        # Extrait une simple moyenne mobile
        closes = data["close"]
        ma = sum(closes)/len(closes)
        return {"ma": ma}
