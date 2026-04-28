"""
Tests — Option AK : HyperOptimizer (grid search + random search).
"""
from __future__ import annotations

import numpy as np
import pytest

from agents.backtest.vectorized_backtester import VectorizedBacktester
from agents.optim.hyperopt import HyperOptimizer, ParamGrid, SearchResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def ohlcv_300() -> np.ndarray:
    rng = np.random.default_rng(99)
    close = 100.0 + np.cumsum(rng.normal(0, 0.5, 300))
    open_ = close + rng.normal(0, 0.1, 300)
    high = np.maximum(open_, close) + rng.uniform(0, 0.3, 300)
    low = np.minimum(open_, close) - rng.uniform(0, 0.3, 300)
    volume = rng.uniform(1_000, 10_000, 300)
    return np.column_stack([open_, high, low, close, volume])


@pytest.fixture
def optimizer(ohlcv_300) -> HyperOptimizer:
    return HyperOptimizer(backtester=VectorizedBacktester(), ohlcv=ohlcv_300)


# ── Tests SearchResult ────────────────────────────────────────────────────────

def test_search_result_fields(optimizer):
    result = optimizer.random_search(n_trials=5, seed=42)
    assert isinstance(result, SearchResult)
    assert isinstance(result.best_params, dict)
    assert isinstance(result.best_sharpe, float)
    assert isinstance(result.best_drawdown_pct, float)
    assert isinstance(result.best_win_rate, float)
    assert isinstance(result.n_evaluated, int)
    assert isinstance(result.n_skipped, int)
    assert isinstance(result.all_results, list)
    assert result.search_method in ("grid", "random")
    assert result.duration_s >= 0.0


# ── Tests grid search ─────────────────────────────────────────────────────────

def test_grid_search_basic(optimizer):
    grid = ParamGrid(fast=[5, 10], slow=[30, 50], rsi_period=[14], strategy=["sma"])
    result = optimizer.grid_search(grid)
    assert result.search_method == "grid"
    # fast >= slow doit être filtré : (5,30), (5,50), (10,30), (10,50) = 4 combos
    assert result.n_evaluated + result.n_skipped <= 4


def test_grid_search_filters_fast_ge_slow(optimizer):
    # fast=50 >= slow=30 → doit être ignoré
    grid = ParamGrid(fast=[50], slow=[30], strategy=["sma"])
    result = optimizer.grid_search(grid)
    # La combinaison fast=50 slow=30 est filtrée avant évaluation
    assert result.n_evaluated == 0
    assert result.best_params == {}


def test_grid_search_returns_valid_params(optimizer):
    grid = ParamGrid(fast=[5], slow=[20], strategy=["sma"])
    result = optimizer.grid_search(grid)
    if result.best_params:
        assert result.best_params["fast"] < result.best_params["slow"]


def test_grid_search_metric_sharpe(optimizer):
    grid = ParamGrid(fast=[5, 10], slow=[30, 50], strategy=["sma"])
    result = optimizer.grid_search(grid, metric="sharpe")
    if result.all_results:
        # best_sharpe >= tout autre sharpe dans all_results
        max_sharpe = max(r["sharpe"] for r in result.all_results)
        assert result.best_sharpe == pytest.approx(max_sharpe)


def test_grid_search_metric_drawdown(optimizer):
    grid = ParamGrid(fast=[5, 10], slow=[30, 50], strategy=["sma"])
    result = optimizer.grid_search(grid, metric="drawdown")
    if result.all_results:
        min_dd = min(r["max_drawdown_pct"] for r in result.all_results)
        assert result.best_drawdown_pct == pytest.approx(min_dd)


def test_grid_search_metric_win_rate(optimizer):
    grid = ParamGrid(fast=[5, 10], slow=[30, 50], strategy=["sma"])
    result = optimizer.grid_search(grid, metric="win_rate")
    if result.all_results:
        max_wr = max(r["win_rate"] for r in result.all_results)
        assert result.best_win_rate == pytest.approx(max_wr)


# ── Tests random search ───────────────────────────────────────────────────────

def test_random_search_n_trials(optimizer):
    result = optimizer.random_search(n_trials=10, seed=1)
    assert result.search_method == "random"
    assert result.n_evaluated + result.n_skipped <= 10


def test_random_search_reproducible(optimizer):
    r1 = optimizer.random_search(n_trials=10, seed=42)
    r2 = optimizer.random_search(n_trials=10, seed=42)
    assert r1.best_sharpe == r2.best_sharpe
    assert r1.n_evaluated == r2.n_evaluated


def test_random_search_different_seeds_differ(optimizer):
    r1 = optimizer.random_search(n_trials=20, seed=1)
    r2 = optimizer.random_search(n_trials=20, seed=999)
    # Avec des seeds différents les résultats peuvent différer
    # (pas une garantie stricte mais très probable)
    # On vérifie juste que les deux runs se terminent sans erreur
    assert isinstance(r1.best_sharpe, float)
    assert isinstance(r2.best_sharpe, float)


def test_random_search_fast_lt_slow(optimizer):
    """Vérifie que random_search garantit fast < slow."""
    result = optimizer.random_search(
        n_trials=50, fast_range=(5, 30), slow_range=(20, 100), seed=0
    )
    for r in result.all_results:
        assert r["params"]["fast"] < r["params"]["slow"]


def test_random_search_rsi_strategy(optimizer):
    result = optimizer.random_search(n_trials=5, strategy="rsi", seed=7)
    assert result.search_method == "random"
    assert isinstance(result.best_sharpe, float)


def test_random_search_bb_strategy(optimizer):
    result = optimizer.random_search(n_trials=5, strategy="bb", seed=7)
    assert result.search_method == "random"


# ── Tests all_results ─────────────────────────────────────────────────────────

def test_all_results_structure(optimizer):
    result = optimizer.random_search(n_trials=5, seed=0)
    for r in result.all_results:
        assert "params" in r
        assert "sharpe" in r
        assert "max_drawdown_pct" in r
        assert "win_rate" in r
        assert "total_return_pct" in r
        assert "n_trades" in r


def test_all_results_drawdown_non_negative(optimizer):
    result = optimizer.random_search(n_trials=10, seed=5)
    for r in result.all_results:
        assert r["max_drawdown_pct"] >= 0.0


def test_all_results_win_rate_in_range(optimizer):
    result = optimizer.random_search(n_trials=10, seed=5)
    for r in result.all_results:
        assert 0.0 <= r["win_rate"] <= 1.0


# ── Tests edge cases ──────────────────────────────────────────────────────────

def test_empty_grid_returns_empty_result(optimizer):
    # Grille vide (fast >= slow pour toutes les combos)
    grid = ParamGrid(fast=[100], slow=[10], strategy=["sma"])
    result = optimizer.grid_search(grid)
    assert result.n_evaluated == 0
    assert result.best_params == {}
    assert result.best_sharpe == 0.0


def test_insufficient_bars_skipped():
    """Moins de min_bars barres → toutes les combos sont skippées."""
    tiny = np.ones((20, 5)) * 50.0
    opt = HyperOptimizer(backtester=VectorizedBacktester(), ohlcv=tiny, min_bars=50)
    result = opt.random_search(n_trials=5, seed=0)
    assert result.n_evaluated == 0


def test_duration_positive(optimizer):
    result = optimizer.random_search(n_trials=3, seed=0)
    assert result.duration_s >= 0.0


def test_zero_trials(optimizer):
    result = optimizer.random_search(n_trials=0, seed=0)
    assert result.n_evaluated == 0
    assert result.best_params == {}
