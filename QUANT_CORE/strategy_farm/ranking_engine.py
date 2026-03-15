class RankingEngine:
    def __init__(self):
        pass

    def rank(self, strategies):
        for s in strategies:
            s["fitness"] = (
                0.3 * s.get("sharpe", 0)
                + 0.2 * s.get("return", 0)
                + 0.2 * s.get("stability", 0)
                - 0.2 * s.get("drawdown", 0)
                + 0.1 * s.get("robustness", 0)
            )
        strategies.sort(key=lambda x: x["fitness"], reverse=True)
        return strategies
