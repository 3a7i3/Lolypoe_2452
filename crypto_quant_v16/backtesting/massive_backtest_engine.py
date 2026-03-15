import pandas as pd
from typing import List, Dict, Any

class MassiveBacktestEngine:
    """
    Exécute des backtests massifs sur un ensemble de stratégies validées.
    """

    def __init__(self, df: pd.DataFrame, fee: float = 0.001):
        self.df = df
        self.fee = fee  # frais par transaction

    # -------------------------
    # Backtest simple pour une stratégie
    # -------------------------
    def backtest_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retourne le PnL simulé, drawdown et métriques de performance
        """
        pnl = 0.0
        drawdown = 0.0
        max_value = 0.0

        # Simuler une logique simple selon le type de signal
        signal_type = strategy.get("signal_type")
        position = 0  # 1 = long, -1 = short
        for i in range(1, len(self.df)):
            close = self.df["close"].iloc[i]
            prev_close = self.df["close"].iloc[i - 1]

            if signal_type == "momentum":
                rsi_buy = strategy.get("rsi_buy", 30)
                rsi_sell = strategy.get("rsi_sell", 70)
                delta = close - prev_close
                if delta < -rsi_buy * 0.01:
                    position = 1
                elif delta > rsi_sell * 0.01:
                    position = -1
            elif signal_type == "breakout":
                lookback = strategy.get("lookback_period", 20)
                high = self.df["high"].rolling(lookback).max().iloc[i]
                low = self.df["low"].rolling(lookback).min().iloc[i]
                if close > high:
                    position = 1
                elif close < low:
                    position = -1
            elif signal_type == "mean_reversion":
                ma = self.df["close"].rolling(strategy.get("lookback_period", 20)).mean().iloc[i]
                threshold = strategy.get("threshold", 0.02)
                if close < ma * (1 - threshold):
                    position = 1
                elif close > ma * (1 + threshold):
                    position = -1

            # Calcul PnL
            change = (close - prev_close) / prev_close * position
            change -= self.fee  # frais
            pnl += change
            max_value = max(max_value, pnl)
            drawdown = min(drawdown, pnl - max_value)

        return {
            "strategy": strategy,
            "pnl": round(pnl, 4),
            "drawdown": round(drawdown, 4)
        }

    # -------------------------
    # Backtest massif
    # -------------------------
    def massive_backtest(self, population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for strat in population:
            result = self.backtest_strategy(strat)
            results.append(result)
        return results

if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    # Données simulées
    data = {
        "timestamp": pd.date_range("2026-01-01", periods=100, freq="H"),
        "open": np.random.rand(100) * 100,
        "high": np.random.rand(100) * 100,
        "low": np.random.rand(100) * 100,
        "close": np.random.rand(100) * 100,
        "volume": np.random.rand(100) * 1000
    }
    df = pd.DataFrame(data)

    # Exemple population
    population = [
        {"signal_type": "momentum", "rsi_buy": 30, "rsi_sell": 70, "weight": 1.0},
        {"signal_type": "breakout", "lookback_period": 20, "weight": 1.2},
        {"signal_type": "mean_reversion", "lookback_period": 20, "threshold": 0.02, "weight": 1.1},
    ]

    backtester = MassiveBacktestEngine(df)
    results = backtester.massive_backtest(population)
    for res in results:
        print(res)
