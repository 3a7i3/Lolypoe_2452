# Pipeline IA — Niveau 3
import sys, os
sys.path.append(os.path.dirname(__file__))
from modules.ai_model import AIModel

# Réutilisation des modules du niveau 1
sys.path.append(os.path.join(os.path.dirname(__file__), '../level_1_functional'))
from modules.data_engine import DataEngine
from modules.feature_engineering import FeatureEngineering

import numpy as np

def make_dataset():
    # Génère un dataset fictif (features, label)
    X = np.random.rand(100, 3)
    y = (X[:,0] + X[:,1] > 1).astype(int)  # Label simple
    return X, y

def run_ai_pipeline():
    print("[PIPELINE_AI] Début pipeline IA Niveau 3")
    X, y = make_dataset()
    model = AIModel()
    model.train(X, y)
    preds = model.predict(X)
    print("Prédictions:", preds[:5])
    print("Importances:", model.feature_importances())

if __name__ == "__main__":
    run_ai_pipeline()
