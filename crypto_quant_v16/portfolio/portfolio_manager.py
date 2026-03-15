from typing import List, Dict, Any

class PortfolioManager:
    """
    Gère plusieurs stratégies et répartit le capital.
    """

    def __init__(self, initial_capital: float = 10000):
        self.capital = initial_capital
        self.allocations = []

    # -------------------------
    # Allocation simple proportionnelle
    # -------------------------
    def allocate_capital(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Répartit le capital en fonction de la performance simulée
        """
        total_score = sum([max(s.get("pnl", 0), 0) for s in strategies])
        allocations = []

        for strat in strategies:
            score = max(strat.get("pnl", 0), 0)
            weight = (score / total_score) if total_score > 0 else 1 / len(strategies)
            allocated_capital = self.capital * weight
            allocations.append({
                "strategy": strat["strategy"],
                "allocated_capital": round(allocated_capital, 2),
                "weight": round(weight, 3),
                "pnl": strat.get("pnl"),
                "drawdown": strat.get("drawdown")
            })
        self.allocations = allocations
        return allocations

    # -------------------------
    # Affichage synthétique du portefeuille
    # -------------------------
    def portfolio_summary(self):
        total_allocated = sum([a["allocated_capital"] for a in self.allocations])
        return {
            "total_capital": self.capital,
            "total_allocated": total_allocated,
            "num_strategies": len(self.allocations)
        }

if __name__ == "__main__":
    # Exemple stratégies backtestées
    strategies = [
        {"strategy": {"signal_type": "momentum"}, "pnl": 1.2, "drawdown": -0.1},
        {"strategy": {"signal_type": "breakout"}, "pnl": 0.8, "drawdown": -0.05},
        {"strategy": {"signal_type": "mean_reversion"}, "pnl": 1.5, "drawdown": -0.2},
    ]

    manager = PortfolioManager(initial_capital=10000)
    allocations = manager.allocate_capital(strategies)
    for alloc in allocations:
        print(alloc)

    print(manager.portfolio_summary())
