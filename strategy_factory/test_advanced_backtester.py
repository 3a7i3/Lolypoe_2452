import pandas as pd
import numpy as np
from strategy_factory.advanced_backtester import AdvancedBacktester

def test_advanced_backtester():
    # Création d'un DataFrame de test
    df = pd.DataFrame({
        "close": np.linspace(100, 110, 20),
        "momentum": np.random.randn(20)
    })
    # Stratégie de test
    strategy = {
        "lookback": 1,
        "indicator": "momentum",
        "threshold": 0.5
    }
    backtester = AdvancedBacktester()
    result = backtester.run(strategy, df)
    metrics = result["metrics"]
    print("Test AdvancedBacktester")
    print("Total PnL:", metrics["total_pnl"])
    print("Sharpe:", metrics["sharpe"])
    print("Max Drawdown:", metrics["max_drawdown"])
    print("Winrate:", metrics["winrate"])
    print("Profit Factor:", metrics["profit_factor"])
    assert isinstance(metrics["total_pnl"], float)
    assert isinstance(metrics["sharpe"], float)
    assert isinstance(metrics["max_drawdown"], float)
    assert isinstance(metrics["winrate"], float)
    assert isinstance(metrics["profit_factor"], float)

if __name__ == "__main__":
    test_advanced_backtester()
