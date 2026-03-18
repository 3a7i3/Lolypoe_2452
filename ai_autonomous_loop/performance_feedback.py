import statistics
from typing import List, Dict, Any

class PerformanceFeedback:
    """
    Analyse les résultats de stratégies et génère un rapport structuré
    avec suggestions d'exploration et axes d'amélioration.
    """
    def analyze(self, strategy_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        report = {
            "avg_sharpe": 0,
            "avg_return": 0,
            "max_drawdown": 0,
            "suggestion": "no results",
            "exploration": [],
            "insights": []
        }
        if not strategy_results:
            report["insights"].append("Aucun résultat à analyser.")
            return report
        sharpes = [r.get("sharpe", 0) for r in strategy_results]
        returns = [r.get("return", 0) for r in strategy_results]
        drawdowns = [r.get("drawdown", 0) for r in strategy_results if "drawdown" in r]
        report["avg_sharpe"] = statistics.mean(sharpes) if sharpes else 0
        report["avg_return"] = statistics.mean(returns) if returns else 0
        report["max_drawdown"] = max(drawdowns) if drawdowns else 0

        # Suggestions intelligentes
        if report["avg_sharpe"] < 1:
            report["suggestion"] = "Augmenter les filtres ou explorer d'autres familles de stratégies."
            report["exploration"].append("Tester des stratégies de type mean-reversion ou multi-factor.")
        elif report["avg_sharpe"] > 2:
            report["suggestion"] = "Explorer plus de risque ou augmenter la diversité."
            report["exploration"].append("Augmenter la part de stratégies momentum ou hybrides.")
        else:
            report["suggestion"] = "Continuer l'exploration actuelle, affiner les paramètres."
            report["exploration"].append("Optimiser les hyperparamètres sur les top stratégies.")

        # Insights additionnels
        if report["avg_return"] < 0.01:
            report["insights"].append("Rendement moyen faible : tester d'autres horizons ou signaux.")
        if report["max_drawdown"] > 0.2:
            report["insights"].append("Drawdown élevé : renforcer les filtres de risque.")
        if len(strategy_results) < 5:
            report["insights"].append("Peu de stratégies validées : relancer la génération avec plus de diversité.")

        return report
