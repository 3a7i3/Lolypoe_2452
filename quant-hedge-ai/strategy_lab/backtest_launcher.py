# backtest_launcher.py
class BacktestLauncher:
    def __init__(self, backtest_engine):
        self.backtest_engine = backtest_engine

    def run(self, strategy, data):
        """
        Lance le backtest et retourne les métriques.
        """
        raise NotImplementedError
