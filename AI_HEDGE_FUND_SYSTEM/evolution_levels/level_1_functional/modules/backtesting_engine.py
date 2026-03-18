# Backtesting Engine — Niveau 1
class BacktestingEngine:
    def run(self, strategies, data):
        # Score = (ma - 1) pour l'exemple
        results = []
        for s in strategies:
            score = data["ma"] - 1
            results.append({"id": s["id"], "score": score})
        return results
