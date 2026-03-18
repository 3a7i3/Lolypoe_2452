class AlphaVault:
    def __init__(self):
        self.storage = []
    def add(self, strategy, score):
        self.storage.append({
            "strategy": strategy,
            "score": score
        })
