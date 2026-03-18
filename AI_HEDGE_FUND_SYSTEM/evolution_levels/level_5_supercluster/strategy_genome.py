# Niveau 5 — StrategyGenomeSystem
import random

class StrategyGenome:
    def __init__(self, indicator, lookback, threshold, risk):
        self.indicator = indicator
        self.lookback = lookback
        self.threshold = threshold
        self.risk = risk

    def mutate(self):
        # Mutation simple d'un paramètre
        self.threshold += random.uniform(-0.05, 0.05)
        self.threshold = max(0, min(1, self.threshold))

    def crossover(self, other):
        # Crossover simple
        child = StrategyGenome(
            indicator=self.indicator,
            lookback=(self.lookback + other.lookback) // 2,
            threshold=(self.threshold + other.threshold) / 2,
            risk=(self.risk + other.risk) / 2
        )
        return child
