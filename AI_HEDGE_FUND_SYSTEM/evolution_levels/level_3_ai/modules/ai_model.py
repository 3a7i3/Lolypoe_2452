# AI Model — Niveau 3
from sklearn.ensemble import RandomForestClassifier
import numpy as np

class AIModel:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=10)

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict_proba(X)[:,1]  # Probabilité du signal

    def feature_importances(self):
        return self.model.feature_importances_
