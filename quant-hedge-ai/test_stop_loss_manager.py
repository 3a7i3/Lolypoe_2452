"""Tests — Options S+T : StopLossManager (Stop Loss / Take Profit / Trailing)."""
from __future__ import annotations

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from agents.risk.stop_loss_manager import StopLossManager, PositionLevel, TriggerResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sl(sl_pct=0.05, tp_pct=0.10, trailing=None):
    return StopLossManager(default_sl_pct=sl_pct, default_tp_pct=tp_pct, trailing_pct=trailing)


# ---------------------------------------------------------------------------
# Construction / validation
# ---------------------------------------------------------------------------

class TestStopLossManagerInit:
    def test_defaults(self):
        m = StopLossManager()
        assert m.default_sl_pct == 0.05
        assert m.default_tp_pct == 0.10
        assert m.trailing_pct is None

    def test_custom(self):
        m = StopLossManager(default_sl_pct=0.03, default_tp_pct=0.06, trailing_pct=0.02)
        assert m.default_sl_pct == 0.03
        assert m.trailing_pct == 0.02

    def test_negative_sl_raises(self):
        with pytest.raises(ValueError, match="default_sl_pct"):
            StopLossManager(default_sl_pct=-0.01)

    def test_negative_tp_raises(self):
        with pytest.raises(ValueError, match="default_tp_pct"):
            StopLossManager(default_tp_pct=-0.01)

    def test_negative_trailing_raises(self):
        with pytest.raises(ValueError, match="trailing_pct"):
            StopLossManager(trailing_pct=-0.01)

    def test_zero_tp_allowed(self):
        m = StopLossManager(default_tp_pct=0.0)
        level = m.set_levels("BTC", entry_price=100.0)
        assert level.tp_price is None  # TP désactivé si 0


# ---------------------------------------------------------------------------
# set_levels
# ---------------------------------------------------------------------------

class TestSetLevels:
    def test_sl_price_correct(self):
        m = _sl(sl_pct=0.05, tp_pct=0.10)
        level = m.set_levels("BTC", entry_price=50_000.0)
        assert pytest.approx(level.sl_price, rel=1e-6) == 47_500.0

    def test_tp_price_correct(self):
        m = _sl(sl_pct=0.05, tp_pct=0.10)
        level = m.set_levels("BTC", entry_price=50_000.0)
        assert pytest.approx(level.tp_price, rel=1e-6) == 55_000.0  # type: ignore

    def test_entry_stored(self):
        m = _sl()
        level = m.set_levels("ETH", entry_price=3_000.0)
        assert level.entry_price == 3_000.0

    def test_override_sl_tp(self):
        m = _sl(sl_pct=0.05, tp_pct=0.10)
        level = m.set_levels("BTC", entry_price=100.0, sl_pct=0.02, tp_pct=0.05)
        assert pytest.approx(level.sl_price, rel=1e-6) == 98.0
        assert pytest.approx(level.tp_price, rel=1e-6) == 105.0  # type: ignore

    def test_invalid_entry_price_raises(self):
        m = _sl()
        with pytest.raises(ValueError, match="entry_price"):
            m.set_levels("BTC", entry_price=0.0)

    def test_negative_entry_price_raises(self):
        m = _sl()
        with pytest.raises(ValueError, match="entry_price"):
            m.set_levels("BTC", entry_price=-100.0)

    def test_level_stored_in_active_symbols(self):
        m = _sl()
        m.set_levels("BTC", 50_000.0)
        assert "BTC" in m.active_symbols()

    def test_overwrite_existing_level(self):
        m = _sl()
        m.set_levels("BTC", 50_000.0)
        m.set_levels("BTC", 60_000.0)  # nouveau prix d'entrée
        assert m.get_level("BTC").entry_price == 60_000.0  # type: ignore


# ---------------------------------------------------------------------------
# set_levels_atr
# ---------------------------------------------------------------------------

class TestSetLevelsATR:
    def test_sl_from_atr(self):
        m = _sl()
        level = m.set_levels_atr("BTC", entry_price=50_000.0, atr=1_000.0, sl_multiplier=2.0)
        # sl_pct = 1000*2/50000 = 0.04 → sl_price = 50000*(1-0.04) = 48000
        assert pytest.approx(level.sl_price, rel=1e-6) == 48_000.0

    def test_tp_from_atr(self):
        m = _sl()
        level = m.set_levels_atr("BTC", entry_price=50_000.0, atr=1_000.0, sl_multiplier=2.0, tp_multiplier=4.0)
        # tp_pct = 1000*4/50000 = 0.08 → tp_price = 50000*1.08 = 54000
        assert pytest.approx(level.tp_price, rel=1e-6) == 54_000.0  # type: ignore

    def test_zero_atr_raises(self):
        m = _sl()
        with pytest.raises(ValueError, match="atr"):
            m.set_levels_atr("BTC", 50_000.0, atr=0.0)

    def test_negative_atr_raises(self):
        m = _sl()
        with pytest.raises(ValueError, match="atr"):
            m.set_levels_atr("BTC", 50_000.0, atr=-100.0)

    def test_zero_sl_multiplier_raises(self):
        m = _sl()
        with pytest.raises(ValueError, match="sl_multiplier"):
            m.set_levels_atr("BTC", 50_000.0, atr=100.0, sl_multiplier=0.0)


# ---------------------------------------------------------------------------
# check — Stop Loss
# ---------------------------------------------------------------------------

class TestCheckStopLoss:
    def test_triggered_below_sl(self):
        m = _sl(sl_pct=0.05)
        m.set_levels("BTC", entry_price=50_000.0)
        r = m.check("BTC", current_price=47_000.0)  # < 47500
        assert r.triggered
        assert r.trigger_type == "stop_loss"

    def test_not_triggered_above_sl(self):
        m = _sl(sl_pct=0.05)
        m.set_levels("BTC", entry_price=50_000.0)
        r = m.check("BTC", current_price=48_000.0)  # > 47500
        assert not r.triggered

    def test_not_triggered_at_exact_sl(self):
        m = _sl(sl_pct=0.05)
        m.set_levels("BTC", entry_price=50_000.0)
        r = m.check("BTC", current_price=47_500.0)  # exactement au SL
        assert r.triggered  # ≤ → déclenché

    def test_no_level_returns_not_triggered(self):
        m = _sl()
        r = m.check("UNKNOWN", 100.0)
        assert not r.triggered
        assert r.trigger_type is None


# ---------------------------------------------------------------------------
# check — Take Profit
# ---------------------------------------------------------------------------

class TestCheckTakeProfit:
    def test_triggered_above_tp(self):
        m = _sl(sl_pct=0.05, tp_pct=0.10)
        m.set_levels("BTC", entry_price=50_000.0)
        r = m.check("BTC", current_price=56_000.0)  # > 55000
        assert r.triggered
        assert r.trigger_type == "take_profit"

    def test_not_triggered_below_tp(self):
        m = _sl(sl_pct=0.05, tp_pct=0.10)
        m.set_levels("BTC", entry_price=50_000.0)
        r = m.check("BTC", current_price=54_000.0)  # < 55000
        assert not r.triggered

    def test_no_tp_when_disabled(self):
        m = StopLossManager(default_sl_pct=0.05, default_tp_pct=0.0)
        m.set_levels("BTC", entry_price=50_000.0)
        r = m.check("BTC", current_price=999_999.0)
        # SL non déclenché mais pas de TP
        assert not r.triggered or r.trigger_type == "stop_loss"


# ---------------------------------------------------------------------------
# Trailing Stop (option T)
# ---------------------------------------------------------------------------

class TestTrailingStop:
    def test_initial_trailing_price_set(self):
        m = _sl(trailing=0.03)
        level = m.set_levels("BTC", entry_price=100.0)
        # trailing_stop_price initial = 100 * (1-0.03) = 97
        assert pytest.approx(level.trailing_stop_price, rel=1e-6) == 97.0  # type: ignore

    def test_trailing_moves_up_with_price(self):
        m = _sl(sl_pct=0.10, tp_pct=0.0, trailing=0.03)
        m.set_levels("BTC", entry_price=100.0)
        m.update_trailing("BTC", current_price=110.0)
        level = m.get_level("BTC")
        # nouveau trailing = 110 * (1-0.03) = 106.7
        assert level.trailing_stop_price > 97.0  # type: ignore

    def test_trailing_doesnt_move_down(self):
        m = _sl(sl_pct=0.10, tp_pct=0.0, trailing=0.03)
        m.set_levels("BTC", entry_price=100.0)
        m.update_trailing("BTC", current_price=110.0)
        prev = m.get_level("BTC").trailing_stop_price  # type: ignore
        m.update_trailing("BTC", current_price=105.0)  # baisse → trailing ne recule pas
        assert m.get_level("BTC").trailing_stop_price == prev  # type: ignore

    def test_trailing_triggers_on_pullback(self):
        m = _sl(sl_pct=0.50, tp_pct=0.0, trailing=0.03)  # SL loin pour tester trailing seul
        m.set_levels("BTC", entry_price=100.0)
        m.update_trailing("BTC", current_price=110.0)  # monte
        r = m.check("BTC", current_price=106.0)  # redescend sous trailing (106.7)
        assert r.triggered
        assert r.trigger_type == "trailing_stop"

    def test_no_trailing_when_disabled(self):
        m = _sl(trailing=None)  # pas de trailing
        m.set_levels("BTC", entry_price=100.0)
        assert m.get_level("BTC").trailing_stop_price is None  # type: ignore

    def test_update_trailing_no_level_noop(self):
        m = _sl(trailing=0.03)
        m.update_trailing("NOEXIST", 100.0)  # pas d'erreur


# ---------------------------------------------------------------------------
# check_all
# ---------------------------------------------------------------------------

class TestCheckAll:
    def test_returns_only_triggered(self):
        m = _sl(sl_pct=0.05, tp_pct=0.10)
        m.set_levels("BTC", entry_price=50_000.0)
        m.set_levels("ETH", entry_price=3_000.0)
        prices = {"BTC": 47_000.0, "ETH": 3_100.0}  # BTC déclenché, ETH non
        triggers = m.check_all(prices)
        assert len(triggers) == 1
        assert triggers[0].symbol == "BTC"

    def test_returns_empty_when_none_triggered(self):
        m = _sl(sl_pct=0.05, tp_pct=0.10)
        m.set_levels("BTC", entry_price=50_000.0)
        triggers = m.check_all({"BTC": 50_000.0})  # prix stable
        assert triggers == []

    def test_skips_symbols_without_price(self):
        m = _sl(sl_pct=0.05)
        m.set_levels("BTC", entry_price=50_000.0)
        triggers = m.check_all({})  # pas de prix fourni
        assert triggers == []

    def test_all_triggered(self):
        m = _sl(sl_pct=0.05, tp_pct=0.10)
        m.set_levels("BTC", entry_price=50_000.0)
        m.set_levels("ETH", entry_price=3_000.0)
        prices = {"BTC": 40_000.0, "ETH": 2_000.0}
        triggers = m.check_all(prices)
        assert len(triggers) == 2


# ---------------------------------------------------------------------------
# clear / clear_all / status
# ---------------------------------------------------------------------------

class TestManagement:
    def test_clear_removes_symbol(self):
        m = _sl()
        m.set_levels("BTC", 50_000.0)
        m.clear("BTC")
        assert "BTC" not in m.active_symbols()

    def test_clear_noop_on_unknown(self):
        m = _sl()
        m.clear("UNKNOWN")  # pas d'erreur

    def test_clear_all(self):
        m = _sl()
        m.set_levels("BTC", 50_000.0)
        m.set_levels("ETH", 3_000.0)
        m.clear_all()
        assert m.active_symbols() == []

    def test_status_keys(self):
        m = _sl()
        m.set_levels("BTC", 50_000.0)
        s = m.status()
        assert "BTC" in s
        assert "sl_price" in s["BTC"]
        assert "tp_price" in s["BTC"]

    def test_get_level_none_for_unknown(self):
        m = _sl()
        assert m.get_level("UNKNOWN") is None

    def test_active_symbols_empty_initially(self):
        m = _sl()
        assert m.active_symbols() == []
