# parallel_executor.py
from multiprocessing import Pool

def run_strategy(strategy):
    # Appelle le backtest sur la stratégie
    raise NotImplementedError

class ParallelExecutor:
    def __init__(self, workers=8):
        self.workers = workers

    def run_batch(self, strategies):
        with Pool(self.workers) as pool:
            results = pool.map(run_strategy, strategies)
        return results
