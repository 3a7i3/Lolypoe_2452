class PerformanceFeedback:
    def analyze(self, strategy_results):
        insights = {}
        if not strategy_results:
            insights["avg_sharpe"] = 0
            insights["suggestion"] = "no results"
            return insights
        avg_sharpe = sum(r.get("sharpe", 0) for r in strategy_results) / len(strategy_results)
        insights["avg_sharpe"] = avg_sharpe
        if avg_sharpe < 1:
            insights["suggestion"] = "increase filters"
        else:
            insights["suggestion"] = "explore more risk"
        return insights
