import random

class StrategyGenerator:
    indicators = ["momentum","mean_reversion","volatility"]
    def generate(self, n=500):
        strategies = []
        for _ in range(n):
            strat = {
                "indicator": random.choice(self.indicators),
                "lookback": random.randint(5,50),
                "threshold": random.uniform(0.1,1.0)
            }
            strategies.append(strat)
        return strategies
