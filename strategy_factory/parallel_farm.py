from multiprocessing import Pool, cpu_count
from strategy_factory.advanced_backtester import AdvancedBacktester

backtester = AdvancedBacktester()

def evaluate_strategy(args):
    strategy, df = args
    result = backtester.run(strategy, df)
    score = result["metrics"]["sharpe"]
    return {
        "strategy": strategy,
        "score": score,
        "metrics": result["metrics"]
    }

class ParallelStrategyFarm:
    def __init__(self, workers=None):
        self.workers = workers if workers is not None else cpu_count()

    def run(self, strategies, df):
        with Pool(self.workers) as pool:
            results = pool.map(
                evaluate_strategy,
                [(s, df) for s in strategies]
            )
        return results
