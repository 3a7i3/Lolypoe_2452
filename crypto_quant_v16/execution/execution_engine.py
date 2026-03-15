from typing import List, Dict, Any

class ExecutionEngine:
    """
    Exécute les stratégies sur le marché.
    Supporte : paper trading et real trading (via API).
    """

    def __init__(self, mode: str = "paper"):
        """
        mode: "paper" ou "real"
        """
        self.mode = mode
        self.trade_log = []

    # -------------------------
    # Exécution d'une stratégie unique
    # -------------------------
    def execute_strategy(self, strategy: Dict[str, Any], capital: float, price: float):
        """
        Simule ou exécute un trade selon la stratégie et le capital alloué
        """
        position_size = capital / price  # Nombre de tokens à acheter
        trade = {
            "strategy_type": strategy.get("signal_type"),
            "capital": capital,
            "price": price,
            "position_size": position_size,
            "mode": self.mode
        }

        # Paper trading : simule l'exécution
        if self.mode == "paper":
            trade["status"] = "executed_simulated"
        else:
            # Ici, appeler API exchange / broker pour exécution réelle
            trade["status"] = "executed_real"

        self.trade_log.append(trade)
        return trade

    # -------------------------
    # Exécution du portefeuille complet
    # -------------------------
    def execute_portfolio(self, allocations: List[Dict[str, Any]], current_price: float):
        executed_trades = []
        for alloc in allocations:
            trade = self.execute_strategy(alloc["strategy"], alloc["allocated_capital"], current_price)
            executed_trades.append(trade)
        return executed_trades

    # -------------------------
    # Historique des trades
    # -------------------------
    def get_trade_log(self):
        return self.trade_log

if __name__ == "__main__":
    # Exemple allocations
    allocations = [
        {"strategy": {"signal_type": "momentum"}, "allocated_capital": 4000},
        {"strategy": {"signal_type": "breakout"}, "allocated_capital": 3500},
        {"strategy": {"signal_type": "mean_reversion"}, "allocated_capital": 2500},
    ]

    engine = ExecutionEngine(mode="paper")
    current_price = 100  # prix du token ou actif

    trades = engine.execute_portfolio(allocations, current_price)
    for t in trades:
        print(t)

    print("Historique complet :", engine.get_trade_log())
