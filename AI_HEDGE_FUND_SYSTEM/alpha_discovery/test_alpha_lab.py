import sys
try:
    import xgboost
except ImportError:
    import unittest
    @unittest.skip("xgboost non installé, test neutralisé")
    class TestAlphaLab(unittest.TestCase):
        def test_neutralise(self):
            self.skipTest("xgboost non installé")
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
"""
Ce test doit être exécuté depuis la racine du projet avec :
    python -m AI_HEDGE_FUND_SYSTEM.alpha_discovery.test_alpha_lab
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report
try:
    from AI_HEDGE_FUND_SYSTEM.alpha_discovery.alpha_lab import AlphaLab
except ImportError:
    import unittest
    @unittest.skip("xgboost non installé, test neutralisé")
    class TestAlphaLab(unittest.TestCase):
        def test_neutralise(self):
            self.skipTest("xgboost non installé")
    AlphaLab = None

def generate_fake_data():
    data = {
        'close': pd.Series([100 + i + (i%5)*2 for i in range(300)])
    }
    return pd.DataFrame(data)

def test_alpha_discovery():
    df = generate_fake_data()
    lab = AlphaLab()
    ranked = lab.run(df)
    print('Alpha signals ranked:')
    names = []
    scores = []
    for name, score in ranked:
        print(f'{name}: {score:.4f}')
        names.append(name)
        scores.append(score)
    assert len(ranked) > 0
    # Visualisation des scores
    plt.figure(figsize=(7, 4))
    bars = plt.bar(names, scores, color='skyblue')
    plt.title('Scores des signaux découverts')
    plt.ylabel('Score (corrélation)')
    plt.xlabel('Signal')
    plt.ylim(-1, 1)
    plt.axhline(0, color='gray', linestyle='--', linewidth=1)
    for bar, score in zip(bars, scores):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{score:.2f}',
                 ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig('alpha_signals_scores.png', dpi=120)
    plt.show()
    # Backtest pipeline pour chaque signal
    from AI_HEDGE_FUND_SYSTEM.alpha_discovery.alpha_backtester import AlphaBacktester
    print('\n=== Backtest de chaque signal ===')
    for name in names:
        print(f'\n--- Signal: {name} ---')
        # Récupère le signal depuis AlphaLab
        lab_signals = {n: s for n, s in ranked}
        signal = None
        # On régénère le signal ML pour analyse avancée
        if name == 'xgboost_signal':
            from AI_HEDGE_FUND_SYSTEM.alpha_discovery.feature_library import FeatureLibrary
            features = FeatureLibrary().compute_features(df).fillna(0)
            returns = df['close'].pct_change().shift(-1).fillna(0)
            from AI_HEDGE_FUND_SYSTEM.alpha_discovery.ml_alpha_model import MLAlphaModel
            ml_model = MLAlphaModel()
            model = ml_model.train(features, returns)
            signal = ml_model.predict_signal(model, features, index=df.index)
        else:
            # Pour les signaux classiques, on les régénère via AlphaLab
            features = AlphaLab().FeatureLibrary().compute_features(df).fillna(0)
            from AI_HEDGE_FUND_SYSTEM.alpha_discovery.signal_generator import SignalGenerator
            signal = SignalGenerator().generate(features).get(name, None)
            if signal is not None and not isinstance(signal, pd.Series):
                signal = pd.Series(signal, index=df.index)
        if signal is None:
            print(f'Signal {name} non trouvé.')
            continue
        backtester = AlphaBacktester()
        bt_df, stats = backtester.run(df, signal)
        print('Stats:', stats)
        # Visualisation de l'equity curve
        plt.figure(figsize=(7,4))
        plt.plot(bt_df['equity'], label='Equity Curve')
        plt.title(f'Equity Curve - {name}')
        plt.xlabel('Index')
        plt.ylabel('Equity')
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'backtest_equity_{name}.png', dpi=120)
        plt.show()
    print('Test AlphaLab: OK')

if __name__ == '__main__':
    test_alpha_discovery()
