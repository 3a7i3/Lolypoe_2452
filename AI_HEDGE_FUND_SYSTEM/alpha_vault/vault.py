class AlphaVault:
    def __init__(self):
        self.alpha_db = []

    def store(self, strategy, score):
        self.alpha_db.append({"strategy": strategy, "score": score})

    def best(self, n=10):
        return sorted(self.alpha_db, key=lambda x: x["score"], reverse=True)[:n]
