class PortfolioDirector:
    def allocate(self, strategies):
        capital = 1.0
        weight = capital / len(strategies)
        allocation = {}
        for s in strategies:
            allocation[s["name"]] = weight
        return allocation
