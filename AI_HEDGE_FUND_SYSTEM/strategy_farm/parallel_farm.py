from multiprocessing import Pool
from .backtester import StrategyBacktester
from .scorer import StrategyScorer

class ParallelStrategyFarm:
    def __init__(self, n_workers=8):
        self.n_workers = n_workers
        self.backtester = StrategyBacktester()
        self.scorer = StrategyScorer()

    def evaluate(self, args):
        strategy, df = args
        trades = self.backtester.test(strategy, df)
        return self.scorer.score(trades)

    def run(self, strategies, df):
        with Pool(self.n_workers) as p:
            scores = p.map(self.evaluate, [(s, df) for s in strategies])
        return scores
