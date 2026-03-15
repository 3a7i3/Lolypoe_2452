# parallel_engine.py
"""
Module pour tester des stratégies en parallèle (multiprocessing + joblib).
"""
from multiprocessing import Pool
from joblib import Parallel, delayed

class ParallelEngine:
    def __init__(self, n_jobs=8):
        self.n_jobs = n_jobs

    def run_multiprocessing(self, strategy_list, run_strategy_func):
        with Pool(self.n_jobs) as p:
            results = p.map(run_strategy_func, strategy_list)
        return results

    def run_joblib(self, strategy_list, run_strategy_func):
        results = Parallel(n_jobs=self.n_jobs)(
            delayed(run_strategy_func)(config)
            for config in strategy_list
        )
        return results
