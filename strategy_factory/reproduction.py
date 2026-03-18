import random
from strategy_factory.genome import StrategyGenome

class ReproductionEngine:
    def crossover(self, g1, g2):
        child = StrategyGenome()
        child.indicator = random.choice([g1.indicator, g2.indicator])
        child.lookback = int((g1.lookback + g2.lookback)/2)
        child.threshold = (g1.threshold + g2.threshold)/2
        child.stop_loss = (g1.stop_loss + g2.stop_loss)/2
        child.take_profit = (g1.take_profit + g2.take_profit)/2
        return child
