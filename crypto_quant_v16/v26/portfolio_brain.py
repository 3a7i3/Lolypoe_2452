from __future__ import annotations

from typing import Dict


def score_asset(trend: str, momentum: str, volatility: str) -> int:
    score = 0
    if trend == "BULLISH":
        score += 2
    if momentum == "STRONG":
        score += 2
    if volatility == "HIGH":
        score += 1
    return max(score, 1)


def allocate_portfolio(scores: Dict[str, int], capital: float = 10000.0) -> Dict[str, float]:
    total = float(sum(scores.values()))
    if total <= 0:
        return {k: 0.0 for k in scores}
    return {asset: round(capital * (score / total), 2) for asset, score in scores.items()}


def apply_risk_limits(allocation: Dict[str, float], capital: float, max_weight: float = 0.35) -> Dict[str, float]:
    max_dollars = capital * max_weight
    clipped = {k: min(v, max_dollars) for k, v in allocation.items()}
    total = sum(clipped.values())
    if total <= capital:
        clipped["USDT"] = round(capital - total, 2)
    return {k: round(v, 2) for k, v in clipped.items()}
