
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import pandas as pd
from strategy_farm.farm_engine import StrategyFarm
from strategy_farm.evolution.evolution import StrategyEvolutionLoop

def test_evolution():
    n = 50
    df = pd.DataFrame({
        "rsi": [0.3, 0.5, 0.7, 0.6, 0.4]*(n//5),
        "momentum": [0.4, 0.6, 0.8, 0.7, 0.5]*(n//5),
        "volatility": [0.2, 0.3, 0.5, 0.4, 0.3]*(n//5),
        "volume": [100, 120, 110, 130, 125]*(n//5),
        "macd": [0.1, 0.2, 0.3, 0.4, 0.5]*(n//5),
        "ema": [0.5, 0.6, 0.7, 0.8, 0.9]*(n//5),
        "sma": [0.2, 0.3, 0.4, 0.5, 0.6]*(n//5),
        "stochastic": [0.7, 0.6, 0.5, 0.4, 0.3]*(n//5),
        "adx": [0.4, 0.5, 0.6, 0.7, 0.8]*(n//5),
        "obv": [10, 20, 30, 40, 50]*(n//5),
        "close": [10, 11, 12, 11.5, 12.2]*(n//5)
    })
    farm = StrategyFarm()
    evolution = StrategyEvolutionLoop(farm)
    final_strats = evolution.run(df, generations=3, n_strategies=30, top=8)
    assert len(final_strats) == 8
    print("Genetic evolution test passed.")

if __name__ == "__main__":
    test_evolution()
