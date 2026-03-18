import sys
import os
sys.path.append(os.path.dirname(__file__))
from modules.data_engine import DataEngine
from modules.feature_engineering import FeatureEngineering
from modules.strategy_generator import StrategyGenerator
from modules.backtesting_engine import BacktestingEngine
from modules.alpha_vault import AlphaVault

# Config
config = {
    "max_drawdown": 0.2,
    "strategies_per_cycle": 5,
    "backtest_window": 365
}

def run_pipeline():
    print("[PIPELINE_MINIMAL] Début exécution pipeline minimal Niveau 1")
    data = DataEngine().fetch()
    features = FeatureEngineering().transform(data)
    strategies = StrategyGenerator().generate(features, n=config["strategies_per_cycle"])
    results = BacktestingEngine().run(strategies, features)
    vault = AlphaVault()
    for r in results:
        vault.store(r)
    best = vault.best(1)
    print("Best strategy:", best)

if __name__ == "__main__":
    run_pipeline()
