class RiskAnalystAI:
    """Analyse les risques (crash, sur-optimisation, clusters, etc.)."""
    def analyze(self, backtest_results):
        # Détecte les stratégies fragiles fictivement
        return {s: {"fragile": False, "risk_cluster": False} for s in backtest_results}
