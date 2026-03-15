import xgboost as xgb
import pandas as pd

class MLAlphaModel:
    def train(self, X, y):
        model = xgb.XGBRegressor()
        model.fit(X, y)
        return model

    def predict_signal(self, model, X, index=None):
        pred = model.predict(X)
        # Signal binaire : 1 si prédiction > 0, sinon 0
        signal = (pred > 0).astype(int)
        # Retourne une Series pandas pour compatibilité pipeline
        if index is not None:
            return pd.Series(signal, index=index)
        return pd.Series(signal)
