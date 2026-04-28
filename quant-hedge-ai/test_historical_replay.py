"""Tests — Option Z : HistoricalReplay."""
from __future__ import annotations
import sys, os
import pytest
sys.path.insert(0, os.path.dirname(__file__))
from agents.simulation.historical_replay import HistoricalReplay, ReplayResult, _compute_sharpe, _compute_drawdown


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _candles(n: int = 60, start: float = 100.0, trend: float = 0.005) -> list[dict]:
    candles = []
    p = start
    for _ in range(n):
        p = p * (1.0 + trend)
        candles.append({"close": str(round(p, 4)), "symbol": "BTCUSDT"})
    return candles


def _flat_candles(n: int = 30, price: float = 100.0) -> list[dict]:
    return [{"close": str(price), "symbol": "BTCUSDT"}] * n


STRAT_TREND = {"entry_indicator": "EMA", "threshold": 0.2, "sl_pct": 0.05, "tp_pct": 0.10}
STRAT_MEAN  = {"entry_indicator": "RSI", "threshold": 0.2}


# ---------------------------------------------------------------------------
# Helpers functions
# ---------------------------------------------------------------------------
class TestComputeSharpe:
    def test_empty_returns_zero(self):
        assert _compute_sharpe([]) == 0.0

    def test_single_return_zero(self):
        assert _compute_sharpe([0.05]) == 0.0

    def test_positive_returns_positive_sharpe(self):
        assert _compute_sharpe([0.01] * 50) > 0

    def test_negative_returns_negative_sharpe(self):
        assert _compute_sharpe([-0.01] * 50) < 0


class TestComputeDrawdown:
    def test_empty_returns_zero(self):
        assert _compute_drawdown([]) == 0.0

    def test_flat_equity_zero_drawdown(self):
        assert _compute_drawdown([100.0] * 10) == 0.0

    def test_declining_equity_positive_drawdown(self):
        curve = [100.0, 90.0, 80.0]
        assert _compute_drawdown(curve) > 0

    def test_max_drawdown_correct(self):
        curve = [100.0, 120.0, 80.0]  # pic à 120, puis chute à 80 → dd = 40/120 = 33%
        dd = _compute_drawdown(curve)
        assert pytest.approx(dd, rel=1e-4) == pytest.approx(1 - 80/120, rel=1e-4)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
class TestInit:
    def test_defaults(self):
        replay = HistoricalReplay(_candles(10))
        assert replay.initial_equity == 10_000.0

    def test_empty_candles_raises(self):
        with pytest.raises(ValueError, match="candles"):
            HistoricalReplay([])

    def test_invalid_equity_raises(self):
        with pytest.raises(ValueError, match="initial_equity"):
            HistoricalReplay(_candles(10), initial_equity=0.0)

    def test_invalid_position_size_raises(self):
        with pytest.raises(ValueError, match="position_size"):
            HistoricalReplay(_candles(10), position_size=0.0)

    def test_invalid_position_size_over_one(self):
        with pytest.raises(ValueError, match="position_size"):
            HistoricalReplay(_candles(10), position_size=1.5)


# ---------------------------------------------------------------------------
# run — structure du résultat
# ---------------------------------------------------------------------------
class TestRunStructure:
    def test_returns_replay_result(self):
        r = HistoricalReplay(_candles(50), STRAT_TREND).run()
        assert isinstance(r, ReplayResult)

    def test_as_dict_has_keys(self):
        r = HistoricalReplay(_candles(50), STRAT_TREND).run()
        d = r.as_dict()
        for k in ("initial_equity", "final_equity", "total_trades", "win_rate", "sharpe", "max_drawdown"):
            assert k in d

    def test_data_mode_replay(self):
        r = HistoricalReplay(_candles(50)).run()
        assert r.data_mode == "replay"

    def test_equity_curve_length(self):
        candles = _candles(50)
        r = HistoricalReplay(candles, STRAT_TREND).run()
        # equity curve = initial + une entrée par bougie
        assert len(r.equity_curve) == len(candles) + 1

    def test_initial_equity_preserved(self):
        r = HistoricalReplay(_candles(30), initial_equity=5_000.0).run()
        assert r.initial_equity == 5_000.0


# ---------------------------------------------------------------------------
# run — logique de trading
# ---------------------------------------------------------------------------
class TestRunLogic:
    def test_trending_market_generates_trades(self):
        r = HistoricalReplay(_candles(50, trend=0.01), STRAT_TREND, position_size=0.10).run()
        assert r.total_trades > 0

    def test_flat_market_minimal_trades(self):
        candles = _flat_candles(30)
        r = HistoricalReplay(candles, STRAT_TREND, position_size=0.10).run()
        # pas de signal → pas de trade (ou 1 fermeture forcée)
        assert r.total_trades <= 2

    def test_win_rate_between_0_and_1(self):
        r = HistoricalReplay(_candles(50, trend=0.005), STRAT_TREND).run()
        assert 0.0 <= r.win_rate <= 1.0

    def test_max_drawdown_non_negative(self):
        r = HistoricalReplay(_candles(50), STRAT_TREND).run()
        assert r.max_drawdown >= 0.0

    def test_custom_signal_fn(self):
        # Signal toujours BUY au premier bar, puis HOLD
        def my_signal(candles, i): return "BUY" if i == 0 else "HOLD"
        r = HistoricalReplay(_candles(20), signal_fn=my_signal).run()
        buy_trades = [t for t in r.trades if t.action == "BUY"]
        assert len(buy_trades) == 1

    def test_mean_reversion_strategy(self):
        candles = _candles(40, trend=-0.003)
        r = HistoricalReplay(candles, STRAT_MEAN, position_size=0.05).run()
        assert isinstance(r, ReplayResult)
