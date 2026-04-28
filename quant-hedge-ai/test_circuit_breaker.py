"""Tests — Option P : Circuit Breaker / Kill Switch."""
from __future__ import annotations

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from agents.risk.circuit_breaker import CircuitBreaker


# ---------------------------------------------------------------------------
# Construction / validation
# ---------------------------------------------------------------------------

class TestCircuitBreakerInit:
    def test_default_values(self):
        cb = CircuitBreaker()
        assert cb.daily_loss_limit == 0.05
        assert cb.drawdown_limit == 0.15
        assert cb.consecutive_losses_limit == 3

    def test_custom_values(self):
        cb = CircuitBreaker(daily_loss_limit=0.02, drawdown_limit=0.10, consecutive_losses=5)
        assert cb.daily_loss_limit == 0.02
        assert cb.drawdown_limit == 0.10
        assert cb.consecutive_losses_limit == 5

    def test_negative_daily_loss_raises(self):
        with pytest.raises(ValueError, match="daily_loss_limit"):
            CircuitBreaker(daily_loss_limit=-0.1)

    def test_negative_drawdown_raises(self):
        with pytest.raises(ValueError, match="drawdown_limit"):
            CircuitBreaker(drawdown_limit=-0.1)

    def test_negative_consecutive_raises(self):
        with pytest.raises(ValueError, match="consecutive_losses"):
            CircuitBreaker(consecutive_losses=-1)

    def test_zero_disables_rule(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.0, consecutive_losses=0)
        assert not cb.is_triggered(current_drawdown_pct=99.0, realized_pnl_today=-999_999.0)


# ---------------------------------------------------------------------------
# Règle 1 : perte journalière
# ---------------------------------------------------------------------------

class TestDailyLossRule:
    def test_triggers_when_daily_loss_exceeded(self):
        cb = CircuitBreaker(daily_loss_limit=0.05, drawdown_limit=0.0, consecutive_losses=0)
        # Perte de 6% sur 100k = -6000
        triggered = cb.is_triggered(
            current_drawdown_pct=0.0,
            realized_pnl_today=-6_000.0,
            initial_balance=100_000.0,
        )
        assert triggered
        assert "perte journalière" in cb.reason()

    def test_ok_below_limit(self):
        cb = CircuitBreaker(daily_loss_limit=0.05, drawdown_limit=0.0, consecutive_losses=0)
        triggered = cb.is_triggered(
            current_drawdown_pct=0.0,
            realized_pnl_today=-4_000.0,  # 4% < 5%
            initial_balance=100_000.0,
        )
        assert not triggered

    def test_positive_pnl_not_triggered(self):
        cb = CircuitBreaker(daily_loss_limit=0.05, drawdown_limit=0.0, consecutive_losses=0)
        triggered = cb.is_triggered(realized_pnl_today=+5_000.0, initial_balance=100_000.0)
        assert not triggered

    def test_zero_balance_no_crash(self):
        cb = CircuitBreaker(daily_loss_limit=0.05, drawdown_limit=0.0, consecutive_losses=0)
        triggered = cb.is_triggered(realized_pnl_today=-100.0, initial_balance=0.0)
        assert not triggered  # division par zéro protégée → pas déclenché


# ---------------------------------------------------------------------------
# Règle 2 : drawdown
# ---------------------------------------------------------------------------

class TestDrawdownRule:
    def test_triggers_when_drawdown_exceeded(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.15, consecutive_losses=0)
        triggered = cb.is_triggered(current_drawdown_pct=16.0)
        assert triggered
        assert "drawdown" in cb.reason()

    def test_ok_at_limit(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.15, consecutive_losses=0)
        triggered = cb.is_triggered(current_drawdown_pct=15.0)
        assert not triggered  # strictement > limite

    def test_ok_below_limit(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.15, consecutive_losses=0)
        triggered = cb.is_triggered(current_drawdown_pct=10.0)
        assert not triggered

    def test_zero_drawdown_limit_disables(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.0, consecutive_losses=0)
        triggered = cb.is_triggered(current_drawdown_pct=99.9)
        assert not triggered


# ---------------------------------------------------------------------------
# Règle 3 : pertes consécutives
# ---------------------------------------------------------------------------

class TestConsecutiveLossesRule:
    def test_triggers_after_n_consecutive_losses(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.0, consecutive_losses=3)
        cb.record_trade_result(-100)
        cb.record_trade_result(-200)
        cb.record_trade_result(-50)
        triggered = cb.is_triggered()
        assert triggered
        assert "pertes consécutives" in cb.reason()

    def test_reset_on_win(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.0, consecutive_losses=3)
        cb.record_trade_result(-100)
        cb.record_trade_result(-100)
        cb.record_trade_result(+50)   # gain → reset
        triggered = cb.is_triggered()
        assert not triggered

    def test_two_losses_not_triggered(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.0, consecutive_losses=3)
        cb.record_trade_result(-100)
        cb.record_trade_result(-100)
        assert not cb.is_triggered()

    def test_zero_limit_disables(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.0, consecutive_losses=0)
        for _ in range(100):
            cb.record_trade_result(-1)
        assert not cb.is_triggered()


# ---------------------------------------------------------------------------
# Multiple règles simultanées
# ---------------------------------------------------------------------------

class TestMultipleRules:
    def test_all_rules_reason_combined(self):
        cb = CircuitBreaker(daily_loss_limit=0.01, drawdown_limit=0.01, consecutive_losses=1)
        cb.record_trade_result(-100)
        triggered = cb.is_triggered(
            current_drawdown_pct=5.0,
            realized_pnl_today=-2_000.0,
            initial_balance=100_000.0,
        )
        assert triggered
        reason = cb.reason()
        assert "|" in reason or "perte" in reason or "drawdown" in reason

    def test_triggers_today_increments(self):
        cb = CircuitBreaker(daily_loss_limit=0.05, drawdown_limit=0.0, consecutive_losses=0)
        cb.is_triggered(realized_pnl_today=-10_000.0, initial_balance=100_000.0)
        cb.is_triggered(realized_pnl_today=-10_000.0, initial_balance=100_000.0)
        assert cb.status()["triggers_today"] >= 2


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_daily(self):
        cb = CircuitBreaker(daily_loss_limit=0.05, drawdown_limit=0.0, consecutive_losses=0)
        cb.is_triggered(realized_pnl_today=-10_000.0, initial_balance=100_000.0)
        cb.reset_daily()
        assert cb.status()["triggers_today"] == 0
        assert not cb.status()["triggered"]

    def test_reset_consecutive(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.0, consecutive_losses=3)
        cb.record_trade_result(-100)
        cb.record_trade_result(-100)
        cb.record_trade_result(-100)
        cb.reset_consecutive()
        assert cb.status()["consecutive_losses"] == 0
        assert not cb.is_triggered()


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

class TestStatus:
    def test_status_keys(self):
        cb = CircuitBreaker()
        status = cb.status()
        for key in ("triggered", "reason", "consecutive_losses", "triggers_today", "limits"):
            assert key in status

    def test_status_limits_correct(self):
        cb = CircuitBreaker(daily_loss_limit=0.03, drawdown_limit=0.12, consecutive_losses=4)
        limits = cb.status()["limits"]
        assert limits["daily_loss_limit"] == 0.03
        assert limits["drawdown_limit"] == 0.12
        assert limits["consecutive_losses_limit"] == 4

    def test_reason_empty_when_ok(self):
        cb = CircuitBreaker()
        cb.is_triggered()  # pas de déclenchement
        assert cb.reason() == ""

    def test_total_trades_recorded(self):
        cb = CircuitBreaker()
        cb.record_trade_result(-100)
        cb.record_trade_result(+200)
        assert cb.status()["total_trades_recorded"] == 2


# ---------------------------------------------------------------------------
# Record trade result edge cases
# ---------------------------------------------------------------------------

class TestRecordTradeResult:
    def test_zero_pnl_not_loss(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.0, consecutive_losses=1)
        cb.record_trade_result(0.0)
        # 0 n'est PAS une perte → pas de déclenchement
        assert not cb.is_triggered()

    def test_very_small_loss(self):
        cb = CircuitBreaker(daily_loss_limit=0.0, drawdown_limit=0.0, consecutive_losses=1)
        cb.record_trade_result(-0.000001)
        assert cb.is_triggered()
