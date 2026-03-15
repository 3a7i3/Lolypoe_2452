# ranker.py
class StrategyRanker:
    def __init__(self, weights):
        self.weights = weights  # {'sharpe': 0.4, 'drawdown': 0.3, ...}

    def rank(self, strategies_metrics):
        """
        Calcule le score final pour chaque stratégie.
        """
        raise NotImplementedError
