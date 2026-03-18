class AlphaVault:
    def __init__(self):
        self.vault = {}

    def store(self, strategy_id, stats):
        self.vault[strategy_id] = stats

    def get_best(self, n=10):
        return sorted(self.vault.items(), key=lambda x: -x[1]['score'])[:n]
