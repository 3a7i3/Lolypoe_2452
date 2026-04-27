"""Tests option O — LivePaperEngine : paper trading avec PnL temps réel."""
from __future__ import annotations

import pytest

from agents.execution.live_paper_engine import LivePaperEngine, TradeRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _buy(engine: LivePaperEngine, symbol: str, size: float, price: float, cycle: int = 1) -> dict:
    order = {"symbol": symbol, "action": "BUY", "size": size}
    return engine.execute(order, mark_price=price, cycle=cycle)


def _sell(engine: LivePaperEngine, symbol: str, size: float, price: float, cycle: int = 2) -> dict:
    order = {"symbol": symbol, "action": "SELL", "size": size}
    return engine.execute(order, mark_price=price, cycle=cycle)


def _hold(engine: LivePaperEngine, symbol: str, price: float) -> dict:
    order = {"symbol": symbol, "action": "HOLD", "size": 0.0}
    return engine.execute(order, mark_price=price)


# ---------------------------------------------------------------------------
# Tests init
# ---------------------------------------------------------------------------


class TestLivePaperEngineInit:
    def test_default_balance(self):
        e = LivePaperEngine()
        assert e.balance == pytest.approx(100_000.0)
        assert e.initial_balance == pytest.approx(100_000.0)

    def test_custom_balance(self):
        e = LivePaperEngine(initial_balance=50_000.0)
        assert e.balance == pytest.approx(50_000.0)

    def test_zero_balance_raises(self):
        with pytest.raises(ValueError):
            LivePaperEngine(initial_balance=0.0)

    def test_negative_balance_raises(self):
        with pytest.raises(ValueError):
            LivePaperEngine(initial_balance=-1.0)

    def test_initial_equity_equals_balance(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        assert e.equity() == pytest.approx(10_000.0)

    def test_initial_realized_pnl_zero(self):
        e = LivePaperEngine()
        assert e.realized_pnl == 0.0

    def test_initial_trade_log_empty(self):
        e = LivePaperEngine()
        assert e.trade_log == []

    def test_initial_equity_curve_has_one_point(self):
        e = LivePaperEngine()
        assert len(e.equity_curve) == 1


# ---------------------------------------------------------------------------
# Tests BUY
# ---------------------------------------------------------------------------


class TestBuyOrders:
    def test_buy_reduces_balance(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 5_000.0)
        assert e.balance == pytest.approx(5_000.0)

    def test_buy_creates_position(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 2.0, 1_000.0)
        assert e.positions.get("BTCUSDT", 0) == pytest.approx(2.0)

    def test_buy_sets_avg_cost(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 3_000.0)
        assert e.avg_cost["BTCUSDT"] == pytest.approx(3_000.0)

    def test_avg_cost_updates_on_second_buy(self):
        e = LivePaperEngine(initial_balance=100_000.0)
        _buy(e, "BTCUSDT", 1.0, 2_000.0)  # avg=2000
        _buy(e, "BTCUSDT", 1.0, 4_000.0)  # avg=(2000+4000)/2=3000
        assert e.avg_cost["BTCUSDT"] == pytest.approx(3_000.0)

    def test_buy_insufficient_balance_rejected(self):
        e = LivePaperEngine(initial_balance=1_000.0)
        state = _buy(e, "BTCUSDT", 1.0, 50_000.0)
        assert e.positions.get("BTCUSDT", 0.0) == 0.0
        assert e.balance == pytest.approx(1_000.0)

    def test_buy_records_trade(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 3_000.0, cycle=5)
        assert len(e.trade_log) == 1
        t = e.trade_log[0]
        assert t.action == "BUY"
        assert t.cycle == 5
        assert t.realized_pnl == 0.0


# ---------------------------------------------------------------------------
# Tests SELL + PnL réalisé
# ---------------------------------------------------------------------------


class TestSellOrders:
    def test_sell_increases_balance(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_500.0)
        assert e.balance > 10_000.0

    def test_profitable_sell_pnl(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_500.0)
        assert e.realized_pnl == pytest.approx(500.0)

    def test_losing_sell_pnl(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 2_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_500.0)
        assert e.realized_pnl == pytest.approx(-500.0)

    def test_sell_removes_position(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_000.0)
        assert e.positions.get("BTCUSDT", 0.0) == pytest.approx(0.0)

    def test_partial_sell_keeps_position(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 2.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_200.0)
        assert e.positions.get("BTCUSDT", 0.0) == pytest.approx(1.0)

    def test_sell_more_than_held_capped(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 5.0, 1_000.0)  # on n'a que 1 → vend 1
        assert e.positions.get("BTCUSDT", 0.0) == pytest.approx(0.0)

    def test_sell_without_position_noop(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        state = _sell(e, "BTCUSDT", 1.0, 1_000.0)
        assert e.balance == pytest.approx(10_000.0)
        assert e.realized_pnl == 0.0

    def test_sell_records_realized_pnl_in_log(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_300.0)
        sells = [t for t in e.trade_log if t.action == "SELL"]
        assert len(sells) == 1
        assert sells[0].realized_pnl == pytest.approx(300.0)


# ---------------------------------------------------------------------------
# Tests HOLD
# ---------------------------------------------------------------------------


class TestHoldOrders:
    def test_hold_does_not_change_balance(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _hold(e, "BTCUSDT", 50_000.0)
        assert e.balance == pytest.approx(10_000.0)

    def test_hold_does_not_create_trade(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _hold(e, "BTCUSDT", 50_000.0)
        assert len(e.trade_log) == 0


# ---------------------------------------------------------------------------
# Tests equity + unrealized PnL
# ---------------------------------------------------------------------------


class TestEquityAndUnrealized:
    def test_equity_includes_position_value(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 2_000.0)
        # Equity = balance(8000) + 1 BTC * 2000 = 10000
        assert e.equity() == pytest.approx(10_000.0)

    def test_unrealized_pnl_positive_when_price_rises(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 2_000.0)
        # Simuler montée du prix via HOLD
        _hold(e, "BTCUSDT", 3_000.0)
        assert e.unrealized_pnl() == pytest.approx(1_000.0)

    def test_unrealized_pnl_negative_when_price_falls(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 2_000.0)
        _hold(e, "BTCUSDT", 1_500.0)
        assert e.unrealized_pnl() == pytest.approx(-500.0)

    def test_unrealized_pnl_zero_no_position(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        assert e.unrealized_pnl() == 0.0


# ---------------------------------------------------------------------------
# Tests total return
# ---------------------------------------------------------------------------


class TestTotalReturn:
    def test_initial_return_zero(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        assert e.total_return_pct() == pytest.approx(0.0)

    def test_positive_return_after_profitable_sell(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_100.0)  # +100
        assert e.total_return_pct() > 0.0

    def test_negative_return_after_loss(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 900.0)  # -100
        assert e.total_return_pct() < 0.0


# ---------------------------------------------------------------------------
# Tests drawdown
# ---------------------------------------------------------------------------


class TestDrawdown:
    def test_no_drawdown_initially(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        assert e.drawdown_pct() == pytest.approx(0.0)

    def test_drawdown_after_loss(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 800.0)  # perte -200
        assert e.drawdown_pct() > 0.0

    def test_max_drawdown_tracks_worst(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 800.0)   # -200
        _buy(e, "BTCUSDT", 1.0, 800.0)
        _sell(e, "BTCUSDT", 1.0, 900.0)   # +100
        assert e.max_drawdown_pct() > 0.0


# ---------------------------------------------------------------------------
# Tests win rate
# ---------------------------------------------------------------------------


class TestWinRate:
    def test_no_trades_win_rate_zero(self):
        e = LivePaperEngine()
        assert e.win_rate() == pytest.approx(0.0)

    def test_all_wins(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_200.0)
        _buy(e, "BTCUSDT", 1.0, 1_200.0)
        _sell(e, "BTCUSDT", 1.0, 1_400.0)
        assert e.win_rate() == pytest.approx(1.0)

    def test_all_losses(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 800.0)
        assert e.win_rate() == pytest.approx(0.0)

    def test_mixed_win_rate(self):
        e = LivePaperEngine(initial_balance=20_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_200.0)  # win
        _buy(e, "BTCUSDT", 1.0, 1_200.0)
        _sell(e, "BTCUSDT", 1.0, 1_100.0)  # loss
        assert e.win_rate() == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Tests equity curve
# ---------------------------------------------------------------------------


class TestEquityCurve:
    def test_equity_curve_grows_with_trades(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_200.0)
        assert len(e.equity_curve) == 3  # initial + buy + sell

    def test_equity_curve_starts_with_initial(self):
        e = LivePaperEngine(initial_balance=5_000.0)
        assert e.equity_curve[0] == pytest.approx(5_000.0)


# ---------------------------------------------------------------------------
# Tests summary()
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_keys(self):
        e = LivePaperEngine()
        s = e.summary()
        for k in ["balance", "equity", "realized_pnl", "unrealized_pnl",
                   "total_return_pct", "drawdown_pct", "max_drawdown_pct",
                   "win_rate", "trade_count", "sell_count"]:
            assert k in s, f"Clé manquante : {k}"

    def test_summary_after_trade(self):
        e = LivePaperEngine(initial_balance=10_000.0)
        _buy(e, "BTCUSDT", 1.0, 1_000.0)
        _sell(e, "BTCUSDT", 1.0, 1_300.0)
        s = e.summary()
        assert s["realized_pnl"] == pytest.approx(300.0)
        assert s["sell_count"] == 1
        assert s["trade_count"] == 2


# ---------------------------------------------------------------------------
# Tests state retourné par execute()
# ---------------------------------------------------------------------------


class TestExecuteReturnState:
    def test_execute_returns_dict(self):
        e = LivePaperEngine()
        state = _buy(e, "BTCUSDT", 0.1, 50_000.0)
        assert isinstance(state, dict)

    def test_execute_state_has_required_keys(self):
        e = LivePaperEngine()
        state = _buy(e, "BTCUSDT", 0.1, 50_000.0)
        for k in ["balance", "positions", "equity", "realized_pnl",
                   "unrealized_pnl", "total_return_pct", "drawdown_pct",
                   "win_rate", "trade_count"]:
            assert k in state


# ---------------------------------------------------------------------------
# Tests runtime_config (option O)
# ---------------------------------------------------------------------------


class TestRuntimeConfigInitialBalance:
    def test_default(self):
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert cfg.initial_balance == pytest.approx(100_000.0)

    def test_env_override(self):
        import os
        from unittest.mock import patch
        from runtime_config import load_runtime_config_from_env
        with patch.dict(os.environ, {"V9_INITIAL_BALANCE": "50000"}):
            cfg = load_runtime_config_from_env()
        assert cfg.initial_balance == pytest.approx(50_000.0)

    def test_as_dict_contains_field(self):
        from runtime_config import RuntimeConfig
        d = RuntimeConfig().as_dict()
        assert "initial_balance" in d
