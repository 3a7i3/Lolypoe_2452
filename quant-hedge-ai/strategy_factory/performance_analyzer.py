from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnalyzerConfig:
    min_sharpe: float = 1.5
    max_drawdown: float = 0.2
    min_win_rate: float = 0.45


class PerformanceAnalyzer:
    """Filters and ranks strategy backtest results."""

    def __init__(self, cfg: AnalyzerConfig | None = None) -> None:
        self.cfg = cfg or AnalyzerConfig()

    def filter_candidates(self, results: list[dict]) -> list[dict]:
        out = []
        for r in results:
            sharpe = float(r.get("sharpe", 0.0))
            drawdown = float(r.get("drawdown", 1.0))
            win_rate = float(r.get("win_rate", 0.0))
            if sharpe >= self.cfg.min_sharpe and drawdown <= self.cfg.max_drawdown and win_rate >= self.cfg.min_win_rate:
                out.append(r)
        return out

    def rank(self, results: list[dict]) -> list[dict]:
        return sorted(
            results,
            key=lambda x: (
                float(x.get("sharpe", -999.0)),
                float(x.get("win_rate", 0.0)),
                -float(x.get("drawdown", 1.0)),
                float(x.get("pnl", -999.0)),
            ),
            reverse=True,
        )
