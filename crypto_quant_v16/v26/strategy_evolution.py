from __future__ import annotations

import random
from typing import Dict, List


INDICATORS = ["EMA", "RSI", "MACD", "BOLLINGER", "VWAP", "ATR"]
RULES = ["cross", "threshold", "breakout", "reversal"]


def generate_strategy() -> Dict[str, str]:
    return {
        "indicator1": random.choice(INDICATORS),
        "indicator2": random.choice(INDICATORS),
        "rule": random.choice(RULES),
    }


def mutate_strategy(strategy: Dict[str, str]) -> Dict[str, str]:
    s = dict(strategy)
    if random.random() < 0.5:
        s["indicator1"] = random.choice(INDICATORS)
    if random.random() < 0.5:
        s["indicator2"] = random.choice(INDICATORS)
    if random.random() < 0.4:
        s["rule"] = random.choice(RULES)
    return s


def backtest_score(strategy: Dict[str, str]) -> float:
    # Synthetic score for rapid prototyping; replace with real backtester later.
    base = random.uniform(0.35, 0.75)
    if strategy["indicator1"] == strategy["indicator2"]:
        base -= 0.08
    if strategy["rule"] == "breakout":
        base += 0.05
    return round(max(0.0, min(1.0, base)), 4)


def evolve_population(population_size: int = 60, keep_top: int = 8) -> List[Dict[str, str | float]]:
    scored = []
    for _ in range(population_size):
        strat = generate_strategy()
        strat = mutate_strategy(strat)
        score = backtest_score(strat)
        scored.append({**strat, "score": score})

    scored.sort(key=lambda x: float(x["score"]), reverse=True)
    return scored[:keep_top]
