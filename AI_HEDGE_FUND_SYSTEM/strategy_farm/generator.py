import random

class StrategyGenerator:
    indicators = ["rsi", "momentum", "volatility", "volume", "macd", "ema", "sma", "stochastic", "adx", "obv"]
    operators = [">", "<", ">=", "<="]
    signal_types = ["cross", "threshold", "range"]

    def generate(self, n=50):
        strategies = []
        for i in range(n):
            num_conds = random.choice([1, 2, 3])
            conditions = []
            for _ in range(num_conds):
                indicator = random.choice(self.indicators)
                operator = random.choice(self.operators)
                threshold = round(random.uniform(0.1, 0.9), 3)
                cond = {
                    "indicator": indicator,
                    "operator": operator,
                    "threshold": threshold
                }
                if random.random() < 0.3:
                    cond["signal_type"] = random.choice(self.signal_types)
                conditions.append(cond)
            strat = {
                "conditions": conditions,
                "logic": random.choice(["AND", "OR"]),
                "position_size": round(random.uniform(0.05, 0.5), 2)
            }
            strategies.append(strat)
        return strategies
