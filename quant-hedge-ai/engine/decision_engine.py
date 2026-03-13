"""Decision Engine - Intelligent orchestration and strategy ranking."""
from __future__ import annotations

from typing import Sequence


class StrategyRanker:
    """Ranks strategies using multi-criteria scoring."""

    @staticmethod
    def composite_score(strategy: dict) -> float:
        """
        Calculate composite score combining multiple metrics.
        Higher is better.
        """
        sharpe = float(strategy.get("sharpe", 0.0))
        drawdown = max(0.01, float(strategy.get("drawdown", 0.01)))
        pnl = float(strategy.get("pnl", 0.0))
        win_rate = float(strategy.get("win_rate", 0.5))

        # Sharpe is most important, penalize drawdown, reward PnL and win rate
        score = (sharpe / drawdown) * (1.0 + win_rate * 0.1 + max(0.0, pnl) * 0.01)
        return round(score, 6)

    def rank(self, strategies: Sequence[dict]) -> list[dict]:
        """Rank strategies by composite score (descending)."""
        scored = [(s, self.composite_score(s)) for s in strategies]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored]


class DecisionEngine:
    """Main orchestrator for intelligent decisions at each cycle."""

    def __init__(
        self,
        min_sharpe: float = 2.0,
        max_drawdown_for_trade: float = 0.1,
        whale_block_threshold: int = 2,
    ) -> None:
        self.ranker = StrategyRanker()
        self.min_sharpe = float(min_sharpe)
        self.max_drawdown_for_trade = float(max_drawdown_for_trade)
        self.whale_block_threshold = int(whale_block_threshold)

    def select_strategies(self, candidates: list[dict], top_n: int = 10) -> list[dict]:
        """Select top N strategies for deployment."""
        ranked = self.ranker.rank(candidates)
        return ranked[:top_n]

    def should_trade(self, best_strategy: dict | None, regime: str, whale_alerts: list[str]) -> bool:
        """
        Decide whether to trade based on strategy quality + market regime.
        """
        if best_strategy is None:
            return False

        sharpe = float(best_strategy.get("sharpe", 0.0))
        dd = float(best_strategy.get("drawdown", 1.0))

        # Don't trade in flash crash or with whale alerts
        if regime == "flash_crash":
            return False

        if len(whale_alerts) > self.whale_block_threshold:
            return False  # Too many anomalies

        # Trade if Sharpe and drawdown pass configured thresholds.
        return sharpe > self.min_sharpe and dd < self.max_drawdown_for_trade

    def compute_risk_limits(self, portfolio_vol: float, max_risk: float = 0.02) -> dict:
        """Compute position size limits based on portfolio volatility."""
        return {
            "max_position_size": round(max_risk / max(0.001, portfolio_vol), 4),
            "stop_loss_pct": round(max_risk * 2, 4),
            "take_profit_pct": round(max_risk * 4, 4),
        }
