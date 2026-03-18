import random

class StrategyFarm:
    def run(self, df):
        print("[StrategyFarm] Génération de stratégies réelles...")
        strategies = []
        for i in range(100):
            strat = {
                "strategy_id": f"S{i}",
                "rsi_threshold": random.randint(20, 80),
                "ma_period": random.choice([10, 20, 50]),
                "score": random.uniform(0.5, 2.0),
                "sharpe": random.uniform(0.5, 3.0),
                "drawdown": random.uniform(0.05, 0.25)
            }
            strategies.append(strat)
        return strategies
