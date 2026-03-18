from sklearn.ensemble import RandomForestClassifier

class StrategyAIModel:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=8
        )

    def train(self, dataset):
        X = dataset.drop("target", axis=1)
        y = dataset["target"]
        self.model.fit(X, y)

    def predict(self, features):
        return self.model.predict_proba(features)[0][1]
