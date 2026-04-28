"""Tests — Option W : RegimeStrategySelector."""
from __future__ import annotations
import sys, os
import pytest
sys.path.insert(0, os.path.dirname(__file__))
from agents.quant.regime_strategy_selector import RegimeStrategySelector, _indicator_family, _regime_score


def _strats(*indicators):
    return [{"entry_indicator": ind, "sharpe": 0.5} for ind in indicators]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class TestIndicatorFamily:
    def test_ema_is_trend(self):
        assert _indicator_family({"entry_indicator": "EMA"}) == "trend"

    def test_rsi_is_mean(self):
        assert _indicator_family({"entry_indicator": "RSI"}) == "mean"

    def test_unknown_is_unknown(self):
        assert _indicator_family({"entry_indicator": "CUSTOM_X"}) == "unknown"

    def test_case_insensitive(self):
        assert _indicator_family({"entry_indicator": "ema"}) == "trend"


class TestRegimeScore:
    def test_trend_in_bull(self):
        assert _regime_score({"entry_indicator": "EMA"}, "bull") == 1.0

    def test_mean_in_sideways(self):
        assert _regime_score({"entry_indicator": "RSI"}, "sideways") == 1.0

    def test_trend_in_bear_penalized(self):
        assert _regime_score({"entry_indicator": "EMA"}, "bear") < 0.8

    def test_unknown_regime_defaults_to_neutral(self):
        score = _regime_score({"entry_indicator": "EMA"}, "UNKNOWN_REGIME")
        assert 0.0 < score <= 1.0


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
class TestInit:
    def test_defaults(self):
        sel = RegimeStrategySelector()
        assert sel.min_score == 0.25
        assert sel.boost_factor == 1.5

    def test_invalid_min_score_low(self):
        with pytest.raises(ValueError, match="min_score"):
            RegimeStrategySelector(min_score=-0.1)

    def test_invalid_min_score_high(self):
        with pytest.raises(ValueError, match="min_score"):
            RegimeStrategySelector(min_score=1.5)

    def test_invalid_boost_factor(self):
        with pytest.raises(ValueError, match="boost_factor"):
            RegimeStrategySelector(boost_factor=0.0)


# ---------------------------------------------------------------------------
# select
# ---------------------------------------------------------------------------
class TestSelect:
    def test_bull_prefers_trend(self):
        strats = _strats("EMA", "RSI", "MACD")
        sel = RegimeStrategySelector()
        result = sel.select(strats, regime="bull")
        # EMA et MACD (trend) doivent être en tête
        assert result[0]["entry_indicator"] in {"EMA", "MACD"}

    def test_sideways_prefers_mean(self):
        strats = _strats("EMA", "RSI", "BB")
        sel = RegimeStrategySelector()
        result = sel.select(strats, regime="sideways")
        assert result[0]["entry_indicator"] in {"RSI", "BB"}

    def test_empty_strategies_returns_empty(self):
        sel = RegimeStrategySelector()
        assert sel.select([], "bull") == []

    def test_top_n_limits_results(self):
        strats = _strats("EMA", "RSI", "MACD", "BB", "VWAP")
        sel = RegimeStrategySelector()
        result = sel.select(strats, regime="bull", top_n=2)
        assert len(result) <= 2

    def test_very_high_min_score_fallback_to_all(self):
        strats = _strats("EMA", "RSI")
        sel = RegimeStrategySelector(min_score=0.99)
        result = sel.select(strats, regime="sideways")
        assert len(result) > 0  # fallback garanti

    def test_volatile_regime_returns_mixed(self):
        strats = _strats("EMA", "RSI", "MACD", "BB")
        sel = RegimeStrategySelector(min_score=0.1)
        result = sel.select(strats, regime="volatile")
        assert len(result) > 0


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------
class TestSummary:
    def test_counts_correct(self):
        strats = _strats("EMA", "RSI", "CUSTOM")
        sel = RegimeStrategySelector()
        s = sel.summary(strats, "bull")
        assert s["trend_following"] == 1
        assert s["mean_reversion"] == 1
        assert s["unknown"] == 1

    def test_regime_optimal_family_bull(self):
        sel = RegimeStrategySelector()
        s = sel.summary([], "bull")
        assert s["regime_optimal_family"] == "trend"

    def test_regime_optimal_family_sideways(self):
        sel = RegimeStrategySelector()
        s = sel.summary([], "sideways")
        assert s["regime_optimal_family"] == "mean"
