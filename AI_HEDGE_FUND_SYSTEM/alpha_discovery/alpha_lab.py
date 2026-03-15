import pandas as pd

from AI_HEDGE_FUND_SYSTEM.alpha_discovery.feature_library import FeatureLibrary
from AI_HEDGE_FUND_SYSTEM.alpha_discovery.signal_generator import SignalGenerator
from AI_HEDGE_FUND_SYSTEM.alpha_discovery.alpha_tester import AlphaTester
from AI_HEDGE_FUND_SYSTEM.alpha_discovery.alpha_ranker import AlphaRanker
from AI_HEDGE_FUND_SYSTEM.alpha_discovery.ml_alpha_model import MLAlphaModel

class AlphaLab:
    def run(self, df):
        features = FeatureLibrary().compute_features(df)
        signals = SignalGenerator().generate(features)
        tester = AlphaTester()
        scores = {}
        returns = df["close"].pct_change().shift(-1)
        # Ajout du signal ML XGBoost
        X = features.fillna(0)
        y = returns.fillna(0)
        ml_model = MLAlphaModel()
        model = ml_model.train(X, y)
        ml_signal = ml_model.predict_signal(model, X, index=df.index)
        signals["xgboost_signal"] = ml_signal
        for name, signal in signals.items():
            # Force le type Series et l'indexation
            if not isinstance(signal, pd.Series):
                signal = pd.Series(signal, index=df.index)
            score = tester.test(signal, returns)
            scores[name] = score
        ranked = AlphaRanker().rank(scores)
        return ranked
