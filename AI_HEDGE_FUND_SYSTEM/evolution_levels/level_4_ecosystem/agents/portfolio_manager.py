# Portfolio Manager — Niveau 4
class PortfolioManager:
    def allocate(self, strategies):
        # Equal allocation
        n = len(strategies)
        return {s["id"]: 1/n for s in strategies}
