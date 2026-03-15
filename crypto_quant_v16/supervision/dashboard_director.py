from typing import List, Dict, Any

class DashboardDirector:
    """
    Panel de supervision central pour monitorer l'ensemble du système :
    - Stratégies
    - Portefeuille
    - Trades
    - Alerts / erreurs
    """

    def __init__(self):
        self.strategies_status = []
        self.portfolio_summary = {}
        self.trades_log = []
        self.alerts = []

    # -------------------------
    # Mettre à jour l'état des stratégies
    # -------------------------
    def update_strategies_status(self, strategies: List[Dict[str, Any]]):
        self.strategies_status = strategies

    # -------------------------
    # Mettre à jour l'état du portefeuille
    # -------------------------
    def update_portfolio(self, portfolio_summary: Dict[str, Any]):
        self.portfolio_summary = portfolio_summary

    # -------------------------
    # Ajouter un trade dans le log
    # -------------------------
    def log_trades(self, trades: List[Dict[str, Any]]):
        self.trades_log.extend(trades)

    # -------------------------
    # Ajouter une alerte
    # -------------------------
    def add_alert(self, alert: str):
        self.alerts.append(alert)

    # -------------------------
    # Affichage synthétique du dashboard
    # -------------------------
    def render_dashboard(self):
        from supervision.alert_manager import AlertManager
        alert_manager = AlertManager()
        alert_manager.add_alert("\n=== DASHBOARD DIRECTOR ===")
        alert_manager.add_alert("STRATEGIES STATUS:")
        for s in self.strategies_status:
            alert_manager.add_alert(f"- {s}")
        alert_manager.add_alert("\nPORTFOLIO SUMMARY:")
        alert_manager.add_alert(str(self.portfolio_summary))
        alert_manager.add_alert("\nTRADES LOG:")
        for t in self.trades_log[-10:]:  # afficher les 10 derniers trades
            alert_manager.add_alert(f"- {t}")
        alert_manager.add_alert("\nALERTS:")
        for a in self.alerts[-10:]:
            alert_manager.add_alert(f"- {a}")
        alert_manager.add_alert("===========================\n")

if __name__ == "__main__":
    dashboard = DashboardDirector()

    # Exemple update stratégies
    strategies = [
        {"strategy": "momentum", "pnl": 1.2, "status": "active"},
        {"strategy": "breakout", "pnl": 0.8, "status": "active"},
    ]
    dashboard.update_strategies_status(strategies)

    # Exemple portfolio
    portfolio_summary = {"total_capital": 10000, "total_allocated": 9500, "num_strategies": 3}
    dashboard.update_portfolio(portfolio_summary)

    # Exemple trade log
    trades = [
        {"token": "TOKEN_1234", "status": "executed_simulated"},
        {"token": "TOKEN_5678", "status": "executed_simulated"},
    ]
    dashboard.log_trades(trades)

    # Exemple alert
    dashboard.add_alert("High risk detected on TOKEN_9999")

    # Affichage dashboard
    dashboard.render_dashboard()
