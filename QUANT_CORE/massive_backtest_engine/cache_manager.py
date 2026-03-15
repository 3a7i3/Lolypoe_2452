class CacheManager:
    def __init__(self):
        self.cache = {}

    def exists(self, strategy_id):
        return strategy_id in self.cache

    def store(self, strategy_id, result):
        self.cache[strategy_id] = result
