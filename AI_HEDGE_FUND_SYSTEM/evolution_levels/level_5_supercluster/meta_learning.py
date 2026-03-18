# Niveau 5 — MetaLearningSystem

class MetaLearningSystem:
    def analyze(self, strategy_results):
        # Simule une analyse des performances passées
        best = max(strategy_results, key=lambda r: r["score"], default=None)
        return best
    def guide(self, history):
        # Simule une guidance pour la prochaine recherche
        return {"suggested_indicator": "momentum", "suggested_lookback": 20}
