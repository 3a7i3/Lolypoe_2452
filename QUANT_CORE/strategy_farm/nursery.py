class Nursery:
    def __init__(self):
        pass

    def generate(self, n=1000):
        # Génère n stratégies simples (RSI, momentum, etc.)
        # Retourne une liste de stratégies
        return []

    def quick_filter(self, strategies):
        # Filtre rapide (sharpe, drawdown, min trades)
        filtered = [s for s in strategies if s.get('sharpe', 1) >= 0.5]
        return filtered
