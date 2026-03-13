"""AI Portfolio Brain - Intelligent allocation using Kelly Criterion + Volatility Targeting."""
from __future__ import annotations


class KellyAllocator:
    """Uses Kelly Criterion for optimal position sizing."""

    def kelly_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly fraction: f = (bp - q) / b
        where:
          b = ratio of win/loss
          p = win rate
          q = 1 - win rate
        """
        if avg_loss <= 0:
            return 0.0

        b = avg_win / avg_loss
        p = max(0.0, min(1.0, win_rate))
        q = 1.0 - p

        kelly = (b * p - q) / b if b > 0 else 0.0
        # Apply fractional Kelly for safety (half-Kelly)
        return max(0.0, min(kelly * 0.5, 0.25))

    def allocate(self, strategy_scores: list[dict]) -> dict[str, float]:
        """
        Allocate capital using Kelly + Sharpe weighting.
        scores: list of {"strategy_id": str, "sharpe": float, "win_rate": float, "drawdown": float}
        """
        if not strategy_scores:
            return {}

        weighted = []
        for item in strategy_scores:
            sharpe = max(0.01, float(item.get("sharpe", 0.01)))
            drawdown = max(0.01, float(item.get("drawdown", 0.01)))
            win_rate = float(item.get("win_rate", 0.5))

            # Composite score: Sharpe / Drawdown * KellyFraction
            kelly_frac = self.kelly_fraction(win_rate, 1.0, 1.0)
            score = (sharpe / drawdown) * (1.0 + kelly_frac)

            weighted.append((item.get("strategy_id", f"strat_{len(weighted)}"), score))

        total_score = sum(s for _, s in weighted) or 1.0
        return {name: round(score / total_score, 4) for name, score in weighted}


class VolatilityTargeter:
    """Adjust position sizes based on realized volatility."""

    def __init__(self, target_vol: float = 0.02) -> None:
        self.target_vol = target_vol

    def adjust_positions(self, allocations: dict[str, float], realized_vol: float) -> dict[str, float]:
        """Scale down positions when volatility is high."""
        if realized_vol <= 0:
            return allocations

        vol_scalar = self.target_vol / realized_vol
        vol_scalar = max(0.5, min(2.0, vol_scalar))  # Clamp between 0.5x and 2x

        return {k: round(v * vol_scalar, 4) for k, v in allocations.items()}


class PortfolioBrain:
    """AI Portfolio Brain - combines Kelly + Volatility targeting + diversification."""

    def __init__(self) -> None:
        self.kelly = KellyAllocator()
        self.vol_target = VolatilityTargeter(target_vol=0.02)

    def compute_allocation(
        self, strategies: list[dict], realized_vol: float, max_strategy_weight: float = 0.3
    ) -> dict[str, float]:
        """
        Compute optimal portfolio allocation.
        strategies: list of strategy results with sharpe, drawdown, win_rate
        """
        # Step 1: Kelly allocation
        allocations = self.kelly.allocate(strategies)

        # Step 2: Volatility targeting
        allocations = self.vol_target.adjust_positions(allocations, realized_vol)

        # Step 3: Diversification cap (no single strategy > max_weight)
        capped = {k: min(max_strategy_weight, v) for k, v in allocations.items()}
        total = sum(capped.values()) or 1.0
        allocations = {k: round(v / total, 4) for k, v in capped.items()}

        return allocations
