class AlphaVault:
    def __init__(self):
        self.database = []
    def store(self, strategy, score):
        self.database.append({
            "strategy": strategy,
            "score": score
        })
