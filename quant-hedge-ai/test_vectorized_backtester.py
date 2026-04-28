"""
Tests — Option AI : VectorizedBacktester numpy.
"""
from __future__ import annotations

import numpy as np
import pytest

from agents.backtest.vectorized_backtester import BacktestConfig, BacktestResult, VectorizedBacktester


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def bt() -> VectorizedBacktester:
    return VectorizedBacktester()


@pytest.fixture
def ohlcv_200() -> np.ndarray:
    """200 barres OHLCV synthétiques reproductibles."""
    rng = np.random.default_rng(42)
    close = 100.0 + np.cumsum(rng.normal(0, 0.5, 200))
    open_ = close + rng.normal(0, 0.1, 200)
    high = np.maximum(open_, close) + rng.uniform(0, 0.3, 200)
    low = np.minimum(open_, close) - rng.uniform(0, 0.3, 200)
    volume = rng.uniform(1_000, 10_000, 200)
    return np.column_stack([open_, high, low, close, volume])


@pytest.fixture
def ohlcv_short() -> np.ndarray:
    """10 barres — trop peu pour la plupart des stratégies."""
    rng = np.random.default_rng(0)
    close = 100.0 + np.cumsum(rng.normal(0, 0.5, 10))
    return np.column_stack([close, close, close, close, np.ones(10)])


# ── Tests BacktestConfig ──────────────────────────────────────────────────────

def test_config_defaults():
    cfg = BacktestConfig()
    assert cfg.strategy == "sma"
    assert cfg.fast == 10
    assert cfg.slow == 30
    assert cfg.initial_capital == 100_000.0
    assert cfg.commission_pct == 0.001


def test_config_custom():
    cfg = BacktestConfig(strategy="rsi", rsi_period=21, initial_capital=50_000.0)
    assert cfg.strategy == "rsi"
    assert cfg.rsi_period == 21
    assert cfg.initial_capital == 50_000.0


# ── Tests résultat structure ──────────────────────────────────────────────────

def test_result_is_dataclass(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig())
    assert isinstance(r, BacktestResult)
    assert isinstance(r.sharpe, float)
    assert isinstance(r.max_drawdown_pct, float)
    assert isinstance(r.win_rate, float)
    assert isinstance(r.total_return_pct, float)
    assert isinstance(r.n_trades, int)
    assert isinstance(r.equity_curve, np.ndarray)
    assert r.duration_bars == 200


def test_equity_curve_length(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig())
    assert len(r.equity_curve) == 200


# ── Tests stratégies ─────────────────────────────────────────────────────────

def test_sma_strategy(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig(strategy="sma", fast=10, slow=30))
    assert r.strategy == "sma"
    assert r.n_trades >= 0
    assert 0.0 <= r.win_rate <= 1.0
    assert r.max_drawdown_pct >= 0.0


def test_rsi_strategy(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig(strategy="rsi", rsi_period=14))
    assert r.strategy == "rsi"
    assert r.max_drawdown_pct >= 0.0


def test_bb_strategy(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig(strategy="bb", bb_period=20, bb_std=2.0))
    assert r.strategy == "bb"
    assert r.max_drawdown_pct >= 0.0


def test_bollinger_alias(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig(strategy="bollinger"))
    assert r.strategy == "bollinger"


def test_unknown_strategy_raises(bt, ohlcv_200):
    with pytest.raises(ValueError, match="Stratégie inconnue"):
        bt.run(ohlcv_200, BacktestConfig(strategy="unknown"))


# ── Tests edge cases ──────────────────────────────────────────────────────────

def test_too_few_bars_returns_zero(bt, ohlcv_short):
    r = bt.run(ohlcv_short, BacktestConfig(strategy="sma", fast=10, slow=30))
    assert r.sharpe == 0.0
    assert r.n_trades == 0
    assert r.max_drawdown_pct == 0.0
    assert r.win_rate == 0.0


def test_flat_prices_no_crash(bt):
    flat = np.ones((100, 5)) * 100.0
    r = bt.run(flat, BacktestConfig())
    assert r.sharpe == 0.0


def test_single_bar_returns_zero(bt):
    one_bar = np.array([[100.0, 101.0, 99.0, 100.0, 1000.0]])
    r = bt.run(one_bar, BacktestConfig())
    assert r.n_trades == 0


def test_list_input_converted(bt):
    """Accepte les listes Python en plus des arrays numpy."""
    data = [[100.0, 101.0, 99.0, 100.0, 1000.0]] * 100
    r = bt.run(data, BacktestConfig(strategy="rsi"))
    assert isinstance(r.sharpe, float)


# ── Tests métriques ───────────────────────────────────────────────────────────

def test_initial_capital_respected(bt, ohlcv_200):
    capital = 50_000.0
    r = bt.run(ohlcv_200, BacktestConfig(initial_capital=capital))
    # La première valeur de l'equity curve doit être proche du capital initial
    assert abs(r.equity_curve[0] - capital) < capital * 0.01


def test_equity_positive(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig())
    assert np.all(r.equity_curve > 0)


def test_drawdown_between_0_and_100(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig())
    assert 0.0 <= r.max_drawdown_pct <= 100.0


def test_win_rate_between_0_and_1(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig())
    assert 0.0 <= r.win_rate <= 1.0


def test_sma_sharpe_finite(bt, ohlcv_200):
    r = bt.run(ohlcv_200, BacktestConfig(fast=5, slow=20))
    assert np.isfinite(r.sharpe)


# ── Tests reproductibilité ────────────────────────────────────────────────────

def test_deterministic(bt, ohlcv_200):
    """Deux runs sur les mêmes données → même résultat."""
    r1 = bt.run(ohlcv_200, BacktestConfig(fast=10, slow=30))
    r2 = bt.run(ohlcv_200, BacktestConfig(fast=10, slow=30))
    assert r1.sharpe == r2.sharpe
    assert r1.n_trades == r2.n_trades


# ── Tests helpers internes ────────────────────────────────────────────────────

def test_compute_max_drawdown_zero_on_rising():
    bt = VectorizedBacktester()
    rising = np.linspace(1, 100, 50)
    dd = bt._compute_max_drawdown(rising)
    assert dd == pytest.approx(0.0, abs=1e-9)


def test_compute_max_drawdown_known():
    bt = VectorizedBacktester()
    equity = np.array([100.0, 120.0, 80.0, 90.0])
    dd = bt._compute_max_drawdown(equity)
    # Drawdown max = (80-120)/120 = -33.3%
    assert dd == pytest.approx(33.333, rel=0.01)


def test_compute_win_rate_empty():
    bt = VectorizedBacktester()
    assert bt._compute_win_rate(np.array([])) == 0.0


def test_compute_win_rate_all_wins():
    bt = VectorizedBacktester()
    assert bt._compute_win_rate(np.array([0.01, 0.02, 0.03])) == 1.0


def test_compute_win_rate_half():
    bt = VectorizedBacktester()
    wr = bt._compute_win_rate(np.array([0.01, -0.01, 0.02, -0.02]))
    assert wr == pytest.approx(0.5)


def test_sharpe_zero_on_flat_returns():
    bt = VectorizedBacktester()
    assert bt._compute_sharpe(np.zeros(100)) == 0.0
