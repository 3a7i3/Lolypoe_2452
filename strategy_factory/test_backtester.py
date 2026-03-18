import pandas as pd
from strategy_factory.backtester import Backtester

def test_backtester_evaluate():
    # Génère un DataFrame factice
    df = pd.DataFrame({
        "momentum": [0.2, 0.3, 0.5, 0.7, 0.9, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7],
        "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]
    })
    strategy = {
        "indicator": "momentum",
        "lookback": 5,
        "threshold": 1.0,
        "stop_loss": 0.02,
        "take_profit": 0.05
    }
    backtester = Backtester()
    pnl = backtester.evaluate(strategy, df)
    assert isinstance(pnl, (int, float))
    print("Test backtester OK, PnL:", pnl)

if __name__ == "__main__":
    test_backtester_evaluate()
