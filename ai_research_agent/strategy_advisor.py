class StrategyAdvisor:
    def __init__(self, hypotheses, strategy_results, context=None):
        self.hypotheses = hypotheses
        self.strategy_results = strategy_results
        self.context = context or {}

    def recommend(self):
        recommendations = []
        for h in self.hypotheses:
            # Exclusion si déjà robuste/testée
            if h not in self.strategy_results:
                # Prise en compte du contexte macro ou regime
                if self.context.get("market_regime") == "panic_bear" and "breakout" in h:
                    continue  # On évite les stratégies breakout en panique
                recommendations.append(f"test_new_strategy:{h}")
        return recommendations
