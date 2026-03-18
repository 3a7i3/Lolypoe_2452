import random

class StrategyGenome:

    indicators = [
        "momentum",
        "mean_reversion",
        "volatility_breakout"
    ]

    def __init__(self):
        self.indicator = random.choice(self.indicators)
        self.lookback = random.randint(5,100)
        self.threshold = random.uniform(0.1,1.5)
        self.stop_loss = random.uniform(0.01,0.05)
        self.take_profit = random.uniform(0.02,0.10)

    def mutate(self):
        if random.random() < 0.3:
            self.lookback += random.randint(-5,5)
        if random.random() < 0.3:
            self.threshold *= random.uniform(0.8,1.2)
        if random.random() < 0.3:
            self.stop_loss *= random.uniform(0.8,1.2)
        return self
