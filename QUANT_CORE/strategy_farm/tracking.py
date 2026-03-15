class StrategyTracker:
    def __init__(self):
        self.tracking = {}

    def track(self, strategy_id, stats):
        self.tracking[strategy_id] = stats

    def get_stats(self, strategy_id):
        return self.tracking.get(strategy_id)
