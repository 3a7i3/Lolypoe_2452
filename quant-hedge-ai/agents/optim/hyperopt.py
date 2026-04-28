"""
Option AK — Optimiseur d'hyperparamètres (grid search + random search).

Optimise les hyperparamètres des stratégies de trading en utilisant
le VectorizedBacktester (option AI) comme fonction objectif.

Méthodes supportées :
  - Grid search  : itère exhaustivement sur une grille de paramètres
  - Random search : échantillonne aléatoirement les paramètres

Usage :
    from agents.optim.hyperopt import HyperOptimizer, ParamGrid
    from agents.backtest.vectorized_backtester import VectorizedBacktester
    import numpy as np

    ohlcv = np.random.randn(300, 5) * 0.5 + 100
    bt = VectorizedBacktester()
    opt = HyperOptimizer(backtester=bt, ohlcv=ohlcv)

    result = opt.grid_search(ParamGrid(fast=[5,10,20], slow=[30,50,100]))
    print(result.best_params, result.best_sharpe)

    result2 = opt.random_search(n_trials=50)
    print(result2.best_params)
"""
from __future__ import annotations

import itertools
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from agents.backtest.vectorized_backtester import BacktestConfig, VectorizedBacktester

logger = logging.getLogger(__name__)


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class ParamGrid:
    fast: list[int] = field(default_factory=lambda: [5, 10, 20])
    slow: list[int] = field(default_factory=lambda: [30, 50, 100])
    rsi_period: list[int] = field(default_factory=lambda: [14])
    strategy: list[str] = field(default_factory=lambda: ["sma"])


@dataclass
class SearchResult:
    best_params: dict
    best_sharpe: float
    best_drawdown_pct: float
    best_win_rate: float
    n_evaluated: int
    n_skipped: int
    all_results: list[dict]
    search_method: str
    duration_s: float


# ── Optimiseur ────────────────────────────────────────────────────────────────

class HyperOptimizer:
    """
    Optimiseur d'hyperparamètres pour stratégies de trading.

    Utilise VectorizedBacktester comme fonction objectif.
    Métriques optimisables : "sharpe", "total_return_pct", "win_rate", "drawdown" (min).
    """

    def __init__(
        self,
        backtester: VectorizedBacktester,
        ohlcv: np.ndarray,
        min_bars: int = 50,
        max_workers: int = 1,
    ) -> None:
        self._bt = backtester
        self._ohlcv = ohlcv
        self._min_bars = min_bars
        self._max_workers = max(1, max_workers)

    # ── Grid search ───────────────────────────────────────────────────────────

    def grid_search(self, grid: ParamGrid, metric: str = "sharpe") -> SearchResult:
        """
        Parcourt toutes les combinaisons valides de la grille.
        Filtre automatiquement fast >= slow (invalide).
        """
        t0 = time.monotonic()

        combos: list[dict] = []
        for strategy, fast, slow, rsi_period in itertools.product(
            grid.strategy, grid.fast, grid.slow, grid.rsi_period
        ):
            if strategy == "sma" and fast >= slow:
                continue  # invalide
            combos.append({
                "strategy": strategy,
                "fast": fast,
                "slow": slow,
                "rsi_period": rsi_period,
            })

        results, n_skipped = self._run_parallel(combos)
        best = self._best_by_metric(results, metric)

        return SearchResult(
            best_params=best.get("params", {}),
            best_sharpe=best.get("sharpe", 0.0),
            best_drawdown_pct=best.get("max_drawdown_pct", 0.0),
            best_win_rate=best.get("win_rate", 0.0),
            n_evaluated=len(results),
            n_skipped=n_skipped,
            all_results=results,
            search_method="grid",
            duration_s=time.monotonic() - t0,
        )

    # ── Random search ─────────────────────────────────────────────────────────

    def random_search(
        self,
        n_trials: int = 50,
        fast_range: tuple[int, int] = (3, 30),
        slow_range: tuple[int, int] = (20, 200),
        rsi_range: tuple[int, int] = (7, 21),
        strategy: str = "sma",
        metric: str = "sharpe",
        seed: int = 42,
    ) -> SearchResult:
        """
        Échantillonne aléatoirement n_trials combinaisons de paramètres.
        fast_range / slow_range / rsi_range : (min, max) inclusifs.
        """
        t0 = time.monotonic()
        rng = random.Random(seed)

        combos: list[dict] = []
        for _ in range(n_trials):
            fast = rng.randint(*fast_range)
            slow = rng.randint(*slow_range)
            # garantit fast < slow
            if fast >= slow:
                slow = fast + rng.randint(5, 50)
            rsi_period = rng.randint(*rsi_range)
            combos.append({
                "strategy": strategy,
                "fast": fast,
                "slow": slow,
                "rsi_period": rsi_period,
            })

        results, n_skipped = self._run_parallel(combos)
        best = self._best_by_metric(results, metric)

        return SearchResult(
            best_params=best.get("params", {}),
            best_sharpe=best.get("sharpe", 0.0),
            best_drawdown_pct=best.get("max_drawdown_pct", 0.0),
            best_win_rate=best.get("win_rate", 0.0),
            n_evaluated=len(results),
            n_skipped=n_skipped,
            all_results=results,
            search_method="random",
            duration_s=time.monotonic() - t0,
        )

    # ── Évaluation ────────────────────────────────────────────────────────────

    def _evaluate(self, params: dict) -> Optional[dict]:
        """Exécute un backtest et retourne les métriques ou None si skip."""
        try:
            cfg = BacktestConfig(
                strategy=params.get("strategy", "sma"),
                fast=params.get("fast", 10),
                slow=params.get("slow", 30),
                rsi_period=params.get("rsi_period", 14),
            )
            result = self._bt.run(self._ohlcv, cfg)
            if result.duration_bars < self._min_bars or result.n_trades == 0:
                return None
            return {
                "params": params,
                "sharpe": result.sharpe,
                "max_drawdown_pct": result.max_drawdown_pct,
                "win_rate": result.win_rate,
                "total_return_pct": result.total_return_pct,
                "n_trades": result.n_trades,
            }
        except Exception as exc:
            logger.debug("HyperOptimizer: skip %s — %s", params, exc)
            return None

    def _run_parallel(self, combos: list[dict]) -> tuple[list[dict], int]:
        """Exécute les évaluations en parallèle si max_workers > 1."""
        results: list[dict] = []
        n_skipped = 0

        if self._max_workers == 1:
            for params in combos:
                out = self._evaluate(params)
                if out is None:
                    n_skipped += 1
                else:
                    results.append(out)
        else:
            with ThreadPoolExecutor(max_workers=self._max_workers) as exe:
                futures = {exe.submit(self._evaluate, p): p for p in combos}
                for fut in as_completed(futures):
                    out = fut.result()
                    if out is None:
                        n_skipped += 1
                    else:
                        results.append(out)

        return results, n_skipped

    def _best_by_metric(self, results: list[dict], metric: str) -> dict:
        """Retourne le meilleur résultat selon la métrique choisie."""
        if not results:
            return {}
        if metric == "drawdown":
            return min(results, key=lambda r: r.get("max_drawdown_pct", float("inf")))
        return max(results, key=lambda r: r.get(metric, float("-inf")))
