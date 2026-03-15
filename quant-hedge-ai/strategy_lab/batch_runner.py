# batch_runner.py
"""
Module pour exécuter les stratégies par lots (batch processing).
"""
class BatchRunner:
    def __init__(self, batch_size=1000):
        self.batch_size = batch_size

    def run_batches(self, strategy_list, run_strategy_func):
        results = []
        for i in range(0, len(strategy_list), self.batch_size):
            batch = strategy_list[i:i+self.batch_size]
            batch_results = [run_strategy_func(config) for config in batch]
            results.extend(batch_results)
        return results
