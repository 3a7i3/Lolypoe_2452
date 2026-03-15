import pandas as pd
import numpy as np
from typing import List, Dict, Any
from advanced_analysis import AdvancedAnalysis

class AlphaDiscovery:
    """
    Génère des signaux / alphas à partir des données et analyses avancées.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.analysis = AdvancedAnalysis(df)

    # ------------------------
    # Signaux Momentum
    # ------------------------
    def momentum_signal(self) -> Dict[str, Any]:
        # RSI simple comme exemple
        delta = self.df['close'].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.rolling(14).mean()
        roll_down = down.rolling(14).mean()
        rs = roll_up / roll_down.replace(0, 1e-8)
        rsi = 100 - (100 / (1 + rs))
        latest_rsi = rsi.iloc[-1]
        signal = "BUY" if latest_rsi < 30 else "SELL" if latest_rsi > 70 else "HOLD"
        return {"momentum_signal": signal, "rsi": float(latest_rsi)}

    # ------------------------
    # Signaux Breakout
    # ------------------------
    def breakout_signal(self) -> Dict[str, Any]:
        high_20 = self.df['high'].rolling(20).max().iloc[-1]
        low_20 = self.df['low'].rolling(20).min().iloc[-1]
        close = self.df['close'].iloc[-1]
        if close > high_20:
            signal = "BUY"
        elif close < low_20:
            signal = "SELL"
        else:
            signal = "HOLD"
        return {"breakout_signal": signal, "high_20": high_20, "low_20": low_20}

    # ------------------------
    # Signaux Mean Reversion
    # ------------------------
    def mean_reversion_signal(self) -> Dict[str, Any]:
        ma20 = self.df['close'].rolling(20).mean().iloc[-1]
        close = self.df['close'].iloc[-1]
        signal = "BUY" if close < ma20*0.98 else "SELL" if close > ma20*1.02 else "HOLD"
        return {"mean_reversion_signal": signal, "ma20": ma20}

    # ------------------------
    # Signaux combinés
    # ------------------------
    def generate_all_signals(self) -> Dict[str, Any]:
        report = {}
        report.update(self.momentum_signal())
        report.update(self.breakout_signal())
        report.update(self.mean_reversion_signal())
        # Ajouter d’autres signaux si besoin (volume spike, whale activity...)
        return report

if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    # Exemple de données simulées
    data = {
        "timestamp": pd.date_range("2026-01-01", periods=100, freq="H"),
        "open": np.random.rand(100) * 100,
        "high": np.random.rand(100) * 100,
        "low": np.random.rand(100) * 100,
        "close": np.random.rand(100) * 100,
        "volume": np.random.rand(100) * 1000
    }
    df = pd.DataFrame(data)

    alpha = AlphaDiscovery(df)
    signals = alpha.generate_all_signals()
    print(signals)
