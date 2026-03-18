
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import pandas as pd
from strategy_farm.generator import StrategyGenerator
from strategy_farm.mutation import StrategyMutation
from strategy_farm.backtester import StrategyBacktester
from strategy_farm.scorer import StrategyScorer
from strategy_farm.selector import StrategySelector
from strategy_farm.farm_engine import StrategyFarm
from strategy_farm.memory import StrategyMemory

def test_strategy_farm():
    # Dummy data
    n = 20
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
    best = farm.run(df, n_strategies=20, top=5)
    print("Best strategies (including AI):")
    for strat in best:
        print(strat)
    assert len(best) == 5
    print("Strategy Farm test passed.")

if __name__ == "__main__":
    test_strategy_farm()
