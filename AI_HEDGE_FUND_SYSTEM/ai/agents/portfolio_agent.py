class PortfolioAgent:
    def allocate(self, strategies, capital=100000):
        print("[PortfolioAgent] Allocating capital...")
        n = len(strategies)
        if n == 0:
            return []
        allocation = capital / n
        for s in strategies:
            print(f"  [PortfolioAgent] {s['strategy']} gets {allocation}")
        return [{"strategy": s["strategy"], "allocation": allocation} for s in strategies]
