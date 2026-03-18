from QUANT_CORE.massive_backtest_engine.batch_manager import BatchManager
from .parallel_executor import ParallelExecutor
from .results_collector import ResultsCollector
from .ranking import StrategyRanker
from .cache_manager import CacheManager

class MassiveBacktestEngine:
    def __init__(self, batch_size=1000, workers=8):
        self.batch_manager = BatchManager(batch_size)
        self.executor = ParallelExecutor(workers)
        self.collector = ResultsCollector()
        self.ranker = StrategyRanker()
        self.cache = CacheManager()

    def run(self, strategies):
        batches = self.batch_manager.create_batches(strategies)
        all_results = []
        for batch in batches:
            results = self.executor.run_batch(batch)
            valid_results = self.collector.collect(results)
            all_results.extend(valid_results)
        ranked = self.ranker.rank(all_results)
        return ranked
