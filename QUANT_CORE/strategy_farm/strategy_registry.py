class StrategyRegistry:
    def __init__(self):
        self.db = {}

    def register(self, strategy):
        self.db[strategy['id']] = strategy

    def get(self, strategy_id):
        return self.db.get(strategy_id)

    def all(self):
        return list(self.db.values())
