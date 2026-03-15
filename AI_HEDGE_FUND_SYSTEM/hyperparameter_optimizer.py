import optuna
import numpy as np

class HyperparameterOptimizer:
    def __init__(self, strategy_generator, n_trials=30, maximize_metric='sharpe'):
        self.strategy_generator = strategy_generator
        self.n_trials = n_trials
        self.maximize_metric = maximize_metric

    def optimize(self, features, returns, df, param_space):
        """
        param_space: dict, e.g. {'min_score': (0.01, 0.2), 'max_strat': (1, 10)}
        """
        def objective(trial):
            params = {}
            for k, v in param_space.items():
                if isinstance(v[0], float):
                    params[k] = trial.suggest_float(k, v[0], v[1])
                else:
                    params[k] = trial.suggest_int(k, v[0], v[1])
            generator = self.strategy_generator(**params)
            strategies = generator.generate(features, returns, df)
            if not strategies:
                return -np.inf
            # Use the best strategy's metric
            best = max(strategies, key=lambda s: s['stats'].get(self.maximize_metric, 0))
            return best['stats'].get(self.maximize_metric, 0)

        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=self.n_trials)
        return study.best_params, study.best_value, study
