class FeatureRegistry:
    def __init__(self):
        self.features = {}
    def add(self, name, score):
        self.features[name] = score
    def best(self):
        return sorted(
            self.features.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
