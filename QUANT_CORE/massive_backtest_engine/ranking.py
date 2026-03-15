class StrategyRanker:
    def rank(self, strategies):
        for s in strategies:
            s["score"] = (
                0.4 * s["sharpe"]
                + 0.3 * s["return"]
                - 0.2 * s["drawdown"]
                + 0.1 * s["winrate"]
            )
        strategies.sort(key=lambda x: x["score"], reverse=True)
        return strategies
