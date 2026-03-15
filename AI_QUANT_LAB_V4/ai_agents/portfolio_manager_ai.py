class PortfolioManagerAI:
    """Optimise l'allocation du capital et la diversification."""
    def allocate(self, backtest_results, risk_report):
        # Alloue 1% à chaque stratégie pour l'exemple
        return {s: 0.01 for s in backtest_results}
