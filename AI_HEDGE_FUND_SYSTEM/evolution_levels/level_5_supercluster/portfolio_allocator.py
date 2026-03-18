# Niveau 5 — PortfolioAllocator

class PortfolioAllocator:
    def allocate(self, strategies):
        total = sum(s["score"] for s in strategies)
        for s in strategies:
            s["weight"] = s["score"] / total if total > 0 else 0
        return strategies
