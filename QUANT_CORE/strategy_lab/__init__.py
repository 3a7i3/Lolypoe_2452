from __future__ import annotations

import copy
import itertools
import logging
import random
from typing import Any, Callable, Dict, List
import numpy as np

INDICATORS = ["RSI", "EMA", "MACD", "VWAP"]

def generate_simple_strategy() -> dict:
    return {
        "indicator": random.choice(INDICATORS),
        "period": random.randint(5, 50),
    }

logger = logging.getLogger(__name__)

class StrategyGenerator:
    """Génère des stratégies robustes avec GA + grid search local."""
    def __init__(self, name: str = "StrategyGenerator", seed: int = 42):
        self.name = name
        self.population: List[Dict[str, Any]] = []
        self.generation = 0
        self._rng = random.Random(seed)
        self.indicators = ["RSI", "EMA", "MACD", "BB", "MOMENTUM"]

    def _random_strategy(self, sid: int, markets: List[str], timeframes: List[str]) -> Dict[str, Any]:
        indicator_count = self._rng.choice([2, 3])
        selected_indicators = self._rng.sample(self.indicators, k=indicator_count)
        raw_weights = np.array([self._rng.uniform(0.1, 1.0) for _ in selected_indicators], dtype=float)
        norm_weights = raw_weights / raw_weights.sum()
        return {
            "id": sid,
            "market": self._rng.choice(markets),
            "timeframe": self._rng.choice(timeframes),
            "indicators": selected_indicators,
            "weights": {k: float(v) for k, v in zip(selected_indicators, norm_weights)},
            "params": {
                "rsi_period": self._rng.randint(8, 30),
                "fast_ema": self._rng.randint(5, 20),
                "slow_ema": self._rng.randint(25, 90),
                "bb_period": self._rng.randint(12, 40),
                "momentum_period": self._rng.randint(5, 40),
                "entry_threshold": round(self._rng.uniform(0.2, 0.8), 2),
                "exit_threshold": round(self._rng.uniform(-0.8, -0.2), 2),
            },
            "risk": {
                "max_position": round(self._rng.uniform(0.05, 0.20), 3),
                "risk_per_trade": round(self._rng.uniform(0.005, 0.03), 4),
                "max_drawdown_stop": round(self._rng.uniform(0.10, 0.25), 3),
            },
            "fitness": 0.0,
            "metrics": {},
            "generation": self.generation,
        }

    def generate_population(self, size: int = 50, markets: List[str] = ["BTC/USDT"], timeframes: List[str] = ["1h"]):
        self.population = [self._random_strategy(i, markets, timeframes) for i in range(size)]
        self.generation += 1
        return self.population
        self.population: List[Dict[str, Any]] = []
        self.generation = 0
        self._rng = random.Random(seed)
        self.indicators = ["RSI", "EMA", "MACD", "BB", "MOMENTUM"]

    def _random_strategy(self, sid: int, markets: List[str], timeframes: List[str]) -> Dict[str, Any]:
        indicator_count = self._rng.choice([2, 3])
        selected_indicators = self._rng.sample(self.indicators, k=indicator_count)
        raw_weights = np.array([self._rng.uniform(0.1, 1.0) for _ in selected_indicators], dtype=float)
        norm_weights = raw_weights / raw_weights.sum()
        return {
            "id": sid,
            "market": self._rng.choice(markets),
            "timeframe": self._rng.choice(timeframes),
            "indicators": selected_indicators,
            "weights": {k: float(v) for k, v in zip(selected_indicators, norm_weights)},
            "params": {
                "rsi_period": self._rng.randint(8, 30),
                "fast_ema": self._rng.randint(5, 20),
                "slow_ema": self._rng.randint(25, 90),
                "bb_period": self._rng.randint(12, 40),
                "momentum_period": self._rng.randint(5, 40),
                "entry_threshold": round(self._rng.uniform(0.2, 0.8), 2),
                "exit_threshold": round(self._rng.uniform(-0.8, -0.2), 2),
            },
            "risk": {
                "max_position": round(self._rng.uniform(0.05, 0.20), 3),
                "risk_per_trade": round(self._rng.uniform(0.005, 0.03), 4),
                "max_drawdown_stop": round(self._rng.uniform(0.10, 0.25), 3),
            },
            "fitness": 0.0,
            "metrics": {},
            "generation": self.generation,
        }

    def generate_population(self, size: int = 50, markets: List[str] = ["BTC/USDT"], timeframes: List[str] = ["1h"]):
        self.population = [self._random_strategy(i, markets, timeframes) for i in range(size)]
        self.generation += 1
        return self.population
