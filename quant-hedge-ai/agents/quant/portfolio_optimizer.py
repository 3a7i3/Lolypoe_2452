from __future__ import annotations


class PortfolioOptimizer:
    """Allocates more weight to high-Sharpe / low-drawdown strategies."""

    def optimize(self, top_results: list[dict]) -> dict[str, float]:
        if not top_results:
            return {}
        scores = []
        for item in top_results:
            sharpe = max(0.01, float(item.get("sharpe", 0.01)))
            dd = max(0.01, float(item.get("drawdown", 0.01)))
            score = sharpe / dd
            label = f"{item['strategy']['entry_indicator']}_{item['strategy']['exit_indicator']}_{item['strategy']['period']}"
            scores.append((label, score))
        total = sum(score for _, score in scores) or 1.0
        return {label: round(score / total, 4) for label, score in scores}
