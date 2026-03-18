import pandas as pd
import numpy as np
from data_engine.market_regime import MarketRegimeDetector
from data_engine.plot_regimes import plot_regimes_and_performance
from strategy_factory.advanced_backtester import AdvancedBacktester

def test_plot_regimes_and_performance():
    # Génère un DataFrame de test
    df = pd.DataFrame({
        "close": np.cumsum(np.random.randn(200)) + 100,
        "momentum": np.random.randn(200)
    })
    strategy = {"lookback": 1, "indicator": "momentum", "threshold": 0.5}
    backtester = AdvancedBacktester()
    result = backtester.run(strategy, df)
    equity_curve = result["equity_curve"]
    plot_regimes_and_performance(df, equity_curve)

if __name__ == "__main__":
    test_plot_regimes_and_performance()
