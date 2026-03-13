from __future__ import annotations

from typing import Iterable, List


class StrategyResearcher:
    """Ranks strategy candidates using Sharpe and drawdown constraints."""

    def rank(self, results: Iterable[dict]) -> List[dict]:
        ranked = sorted(
            results,
            key=lambda x: (float(x.get("sharpe", -999.0)), -float(x.get("drawdown", 1.0))),
            reverse=True,
        )
        return ranked

    def best(self, results: Iterable[dict]) -> dict | None:
        ranked = self.rank(results)
        return ranked[0] if ranked else None
