# engine.py
from batch_manager import BatchManager
from parallel_executor import ParallelExecutor
from results_collector import ResultsCollector
from ranking import StrategyRanker

class MassiveBacktestEngine:
    def __init__(self):
        self.batch_manager = BatchManager()
        self.executor = ParallelExecutor()
        self.collector = ResultsCollector()
        self.ranker = StrategyRanker()

    def run(self, strategies):
        batches = self.batch_manager.create_batches(strategies)
        all_results = []
        for batch in batches:
            results = self.executor.run_batch(batch)
            valid_results = self.collector.collect(results)
            all_results.extend(valid_results)
        ranked = self.ranker.rank(all_results)
        return ranked
