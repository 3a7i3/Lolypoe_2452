import random
from QUANT_CORE.massive_backtest_engine.engine import MassiveBacktestEngine

def mock_backtest(strategy):
    # Simulate a backtest result
    return {
        "strategy_id": strategy["id"],
        "return": random.uniform(-0.2, 1.0),
        "sharpe": random.uniform(0.5, 2.5),
        "drawdown": random.uniform(0.05, 0.3),
        "winrate": random.uniform(0.4, 0.7)
    }

# Patch run_strategy in parallel_executor for testing
import sys
import types
mock_parallel_executor = types.SimpleNamespace(run_strategy=mock_backtest)
sys.modules["QUANT_CORE.massive_backtest_engine.parallel_executor"] = mock_parallel_executor

def test_massive_backtest_engine():
    strategies = [{"id": i} for i in range(50)]
    engine = MassiveBacktestEngine(batch_size=10, workers=4)
    ranked = engine.run(strategies)
    assert len(ranked) == 50
    assert all("score" in s for s in ranked)
    print("Top 5 strategies:")
    for s in ranked[:5]:
        print(s)

if __name__ == "__main__":
    test_massive_backtest_engine()
