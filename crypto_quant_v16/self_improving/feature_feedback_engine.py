class FeatureFeedbackEngine:
    def __init__(self):
        self.feature_scores = {}

    def evaluate_feature(self, feature_name, score):
        self.feature_scores[feature_name] = score

    def select_features(self):
        return [f for f, s in self.feature_scores.items() if s > 0.5]
