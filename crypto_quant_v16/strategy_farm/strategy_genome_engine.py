import random
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai')))
from alpha_discovery import AlphaDiscovery
import pandas as pd

class StrategyGenomeEngine:
    """
    Génère automatiquement des stratégies à partir des signaux Alpha.
    Chaque stratégie est un dictionnaire contenant :
    - type_signal : momentum, breakout, mean_reversion
    - paramètres : seuils, périodes, poids
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.alpha = AlphaDiscovery(df)

    def generate_strategy(self, signal_type: str) -> Dict[str, Any]:
        """
        Génère une stratégie pour un type de signal donné
        """
        if signal_type == "momentum":
            threshold_buy = random.randint(20, 35)  # RSI seuil achat
            threshold_sell = random.randint(65, 80) # RSI seuil vente
            return {
                "signal_type": "momentum",
                "rsi_buy": threshold_buy,
                "rsi_sell": threshold_sell,
                "weight": round(random.uniform(0.5, 1.5), 2)
            }

        elif signal_type == "breakout":
            lookback = random.choice([10, 20, 30])
            return {
                "signal_type": "breakout",
                "lookback_period": lookback,
                "weight": round(random.uniform(0.5, 1.5), 2)
            }

        elif signal_type == "mean_reversion":
            lookback = random.choice([15, 20, 25])
            return {
                "signal_type": "mean_reversion",
                "lookback_period": lookback,
                "threshold": round(random.uniform(0.01, 0.05), 3),
                "weight": round(random.uniform(0.5, 1.5), 2)
            }
        else:
            return {"signal_type": "unknown"}

    def generate_population(self, population_size: int = 50) -> List[Dict[str, Any]]:
        """
        Génère une population complète de stratégies
        """
        population = []
        signal_types = ["momentum", "breakout", "mean_reversion"]
        for _ in range(population_size):
            signal = random.choice(signal_types)
            strategy = self.generate_strategy(signal)
            population.append(strategy)
        return population

if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    # Exemple données simulées
    data = {
        "timestamp": pd.date_range("2026-01-01", periods=100, freq="H"),
        "open": np.random.rand(100) * 100,
        "high": np.random.rand(100) * 100,
        "low": np.random.rand(100) * 100,
        "close": np.random.rand(100) * 100,
        "volume": np.random.rand(100) * 1000
    }
    df = pd.DataFrame(data)

    genome = StrategyGenomeEngine(df)
    population = genome.generate_population(10)
    for i, strat in enumerate(population):
        print(f"Strategy {i+1}: {strat}")
