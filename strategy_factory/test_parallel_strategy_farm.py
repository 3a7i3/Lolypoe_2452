import pandas as pd
import numpy as np
from strategy_factory.parallel_farm import ParallelStrategyFarm

def test_parallel_strategy_farm():
    # DataFrame de test
    df = pd.DataFrame({
        "close": np.linspace(100, 110, 20),
        "momentum": np.random.randn(20)
    })
    # Génère 10 stratégies de test
    strategies = [
        {"lookback": 1, "indicator": "momentum", "threshold": t}
        for t in np.linspace(0.1, 1.0, 10)
    ]
    farm = ParallelStrategyFarm(workers=2)
    results = farm.run(strategies, df)
    print("Test ParallelStrategyFarm")
    for r in results:
        print(r)
    assert len(results) == 10
    assert all("score" in r for r in results)
    assert all("metrics" in r for r in results)

if __name__ == "__main__":
    test_parallel_strategy_farm()
