# Feature Scientist — Niveau 4
class FeatureScientist:
    def extract(self, data):
        closes = data["close"]
        return {"ma": sum(closes)/len(closes), "vol": max(closes)-min(closes)}
