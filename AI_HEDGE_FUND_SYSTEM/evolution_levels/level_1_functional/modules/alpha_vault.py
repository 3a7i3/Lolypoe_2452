# Alpha Vault — Niveau 1
class AlphaVault:
    def __init__(self):
        self.vault = {}
    def store(self, strategy):
        self.vault[strategy["id"]] = strategy
    def best(self, n=1):
        return sorted(self.vault.values(), key=lambda x: -x["score"])[:n]
