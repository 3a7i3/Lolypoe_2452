class StrategyMemory:
    def __init__(self):
        self.memory = {}

    def store(self, strategy_id, result):
        self.memory[strategy_id] = result

    def get_best(self, n=10):
        return sorted(
            self.memory.items(),
            key=lambda x: x[1].get("sharpe", 0),
            reverse=True
        )[:n]

    def already_tested(self, strategy_id):
        return strategy_id in self.memory
