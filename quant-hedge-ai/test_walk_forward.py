"""Tests — Option U : WalkForwardOptimizer."""
from __future__ import annotations

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from agents.quant.walk_forward import WalkForwardOptimizer, _metrics, _returns_from_candles


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candles(n: int = 100, start: float = 100.0, trend: float = 0.001) -> list[dict]:
    """Série de bougies synthétiques avec tendance légèrement haussière."""
    candles = []
    price = start
    for i in range(n):
        price = price * (1.0 + trend)
        candles.append({"symbol": "BTCUSDT", "close": str(round(price, 4)), "volume": "1000"})
    return candles


STRATEGY_TREND = {"entry_indicator": "EMA", "threshold": 0.1}
STRATEGY_MEAN = {"entry_indicator": "RSI", "threshold": 0.5}


# ---------------------------------------------------------------------------
# _metrics helper
# ---------------------------------------------------------------------------

class TestMetrics:
    def test_empty_returns_zeros(self):
        m = _metrics([])
        assert m["sharpe"] == 0.0
        assert m["drawdown"] == 0.0
        assert m["win_rate"] == 0.0

    def test_positive_returns_positive_sharpe(self):
        returns = [0.01] * 50
        m = _metrics(returns)
        assert m["sharpe"] > 0

    def test_negative_returns_negative_sharpe(self):
        returns = [-0.01] * 50
        m = _metrics(returns)
        assert m["sharpe"] < 0

    def test_drawdown_positive(self):
        returns = [0.05, -0.10, 0.03]
        m = _metrics(returns)
        assert m["drawdown"] >= 0

    def test_win_rate_all_positive(self):
        returns = [0.01, 0.02, 0.03]
        m = _metrics(returns)
        assert m["win_rate"] == 1.0

    def test_win_rate_all_negative(self):
        returns = [-0.01, -0.02]
        m = _metrics(returns)
        assert m["win_rate"] == 0.0


# ---------------------------------------------------------------------------
# _returns_from_candles helper
# ---------------------------------------------------------------------------

class TestReturnsFromCandles:
    def test_basic_returns(self):
        candles = [
            {"close": "100.0"},
            {"close": "110.0"},
            {"close": "105.5"},
        ]
        returns = _returns_from_candles(candles)
        assert len(returns) == 2
        assert pytest.approx(returns[0], rel=1e-5) == 0.10

    def test_empty_candles(self):
        assert _returns_from_candles([]) == []

    def test_single_candle(self):
        assert _returns_from_candles([{"close": "100"}]) == []

    def test_zero_price_skipped(self):
        candles = [{"close": "0.0"}, {"close": "100.0"}, {"close": "110.0"}]
        returns = _returns_from_candles(candles)
        # Première paire skippée (division par zéro)
        assert len(returns) == 1


# ---------------------------------------------------------------------------
# Construction / validation
# ---------------------------------------------------------------------------

class TestWalkForwardOptimizerInit:
    def test_defaults(self):
        wfo = WalkForwardOptimizer()
        assert wfo.n_splits == 5
        assert wfo.train_ratio == 0.7
        assert wfo.min_oos_bars == 10

    def test_custom(self):
        wfo = WalkForwardOptimizer(n_splits=3, train_ratio=0.8, min_oos_bars=5)
        assert wfo.n_splits == 3
        assert wfo.train_ratio == 0.8

    def test_invalid_n_splits(self):
        with pytest.raises(ValueError, match="n_splits"):
            WalkForwardOptimizer(n_splits=1)

    def test_invalid_train_ratio_low(self):
        with pytest.raises(ValueError, match="train_ratio"):
            WalkForwardOptimizer(train_ratio=0.05)

    def test_invalid_train_ratio_high(self):
        with pytest.raises(ValueError, match="train_ratio"):
            WalkForwardOptimizer(train_ratio=1.0)

    def test_invalid_min_oos_bars(self):
        with pytest.raises(ValueError, match="min_oos_bars"):
            WalkForwardOptimizer(min_oos_bars=0)


# ---------------------------------------------------------------------------
# _make_splits
# ---------------------------------------------------------------------------

class TestMakeSplits:
    def test_returns_correct_count(self):
        wfo = WalkForwardOptimizer(n_splits=3, min_oos_bars=5)
        candles = _make_candles(100)
        splits = wfo._make_splits(candles)
        assert len(splits) <= 3

    def test_each_split_is_tuple(self):
        wfo = WalkForwardOptimizer(n_splits=3, min_oos_bars=2)
        candles = _make_candles(60)
        splits = wfo._make_splits(candles)
        for train, test in splits:
            assert isinstance(train, list)
            assert isinstance(test, list)

    def test_test_size_respects_min_oos(self):
        wfo = WalkForwardOptimizer(n_splits=5, min_oos_bars=10)
        candles = _make_candles(100)
        splits = wfo._make_splits(candles)
        for _, test in splits:
            assert len(test) >= wfo.min_oos_bars

    def test_empty_data_returns_empty(self):
        wfo = WalkForwardOptimizer(n_splits=3)
        assert wfo._make_splits([]) == []

    def test_insufficient_data_returns_empty(self):
        wfo = WalkForwardOptimizer(n_splits=5, min_oos_bars=50)
        candles = _make_candles(10)
        splits = wfo._make_splits(candles)
        assert splits == []


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

class TestRun:
    def test_returns_expected_keys(self):
        wfo = WalkForwardOptimizer(n_splits=3)
        candles = _make_candles(120)
        result = wfo.run(STRATEGY_TREND, candles)
        for key in ("oos_sharpes", "mean_sharpe", "stability", "n_splits_used", "data_mode"):
            assert key in result

    def test_n_splits_used_positive(self):
        wfo = WalkForwardOptimizer(n_splits=3, min_oos_bars=5)
        candles = _make_candles(120)
        result = wfo.run(STRATEGY_TREND, candles)
        assert result["n_splits_used"] > 0

    def test_data_mode_real(self):
        wfo = WalkForwardOptimizer(n_splits=3, min_oos_bars=5)
        candles = _make_candles(120)
        result = wfo.run(STRATEGY_TREND, candles)
        assert result["data_mode"] == "real"

    def test_insufficient_data_returns_insufficient(self):
        wfo = WalkForwardOptimizer(n_splits=5)
        candles = _make_candles(3)
        result = wfo.run(STRATEGY_TREND, candles)
        assert result["data_mode"] == "insufficient"
        assert result["n_splits_used"] == 0
        assert result["mean_sharpe"] == 0.0

    def test_stability_between_0_and_1(self):
        wfo = WalkForwardOptimizer(n_splits=3, min_oos_bars=5)
        candles = _make_candles(120)
        result = wfo.run(STRATEGY_TREND, candles)
        assert 0.0 <= result["stability"] <= 1.0

    def test_oos_sharpes_length_matches_splits_used(self):
        wfo = WalkForwardOptimizer(n_splits=4, min_oos_bars=5)
        candles = _make_candles(120)
        result = wfo.run(STRATEGY_TREND, candles)
        assert len(result["oos_sharpes"]) == result["n_splits_used"]

    def test_mean_drawdown_non_negative(self):
        wfo = WalkForwardOptimizer(n_splits=3, min_oos_bars=5)
        candles = _make_candles(120)
        result = wfo.run(STRATEGY_TREND, candles)
        assert result["mean_drawdown"] >= 0

    def test_sharpe_std_present(self):
        wfo = WalkForwardOptimizer(n_splits=3, min_oos_bars=5)
        candles = _make_candles(120)
        result = wfo.run(STRATEGY_TREND, candles)
        assert "sharpe_std" in result
        assert result["sharpe_std"] >= 0

    def test_mean_reversion_strategy(self):
        wfo = WalkForwardOptimizer(n_splits=3, min_oos_bars=5)
        candles = _make_candles(120, trend=0.0)
        result = wfo.run(STRATEGY_MEAN, candles)
        assert result["data_mode"] in ("real", "insufficient")


# ---------------------------------------------------------------------------
# is_robust
# ---------------------------------------------------------------------------

class TestIsRobust:
    def test_insufficient_not_robust(self):
        wfo = WalkForwardOptimizer(n_splits=3)
        result = {"data_mode": "insufficient", "stability": 0.8, "mean_sharpe": 1.0}
        assert not wfo.is_robust(result)

    def test_robust_when_passes_thresholds(self):
        wfo = WalkForwardOptimizer()
        result = {
            "data_mode": "real",
            "stability": 0.8,
            "mean_sharpe": 1.2,
            "n_splits_used": 4,
        }
        assert wfo.is_robust(result, min_stability=0.6, min_mean_sharpe=0.5)

    def test_not_robust_low_stability(self):
        wfo = WalkForwardOptimizer()
        result = {"data_mode": "real", "stability": 0.3, "mean_sharpe": 1.5}
        assert not wfo.is_robust(result, min_stability=0.6)

    def test_not_robust_low_sharpe(self):
        wfo = WalkForwardOptimizer()
        result = {"data_mode": "real", "stability": 0.8, "mean_sharpe": 0.1}
        assert not wfo.is_robust(result, min_stability=0.6, min_mean_sharpe=0.5)

    def test_custom_thresholds(self):
        wfo = WalkForwardOptimizer()
        result = {"data_mode": "real", "stability": 0.5, "mean_sharpe": 0.4}
        assert wfo.is_robust(result, min_stability=0.4, min_mean_sharpe=0.3)
