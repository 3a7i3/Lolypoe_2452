"""Tests options H (TelegramNotifier) et J (backtest data_mode + rapport director)."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from agents.notifications.telegram_notifier import TelegramNotifier
from agents.quant.backtest_lab import BacktestLab


# ===========================================================================
# Tests TelegramNotifier (option H)
# ===========================================================================


def _make_notifier(token="abc:TOKEN", chat_id="@chan", cooldown=0.0) -> TelegramNotifier:
    return TelegramNotifier(bot_token=token, chat_id=chat_id, cooldown_seconds=cooldown)


class TestTelegramNotifierEnabled:
    def test_enabled_with_credentials(self):
        n = _make_notifier()
        assert n.enabled is True

    def test_disabled_without_token(self):
        n = TelegramNotifier(bot_token="", chat_id="@chan")
        assert n.enabled is False

    def test_disabled_without_chat_id(self):
        n = TelegramNotifier(bot_token="abc:TOKEN", chat_id="")
        assert n.enabled is False

    def test_disabled_both_empty(self):
        n = TelegramNotifier()
        assert n.enabled is False

    def test_send_disabled_returns_false(self):
        n = TelegramNotifier()
        assert n.send("hello") is False


class TestTelegramNotifierSend:
    def test_send_success(self):
        n = _make_notifier(cooldown=0.0)
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = n.send("test message")

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "chat_id" in call_kwargs.kwargs.get("json", {})
        assert call_kwargs.kwargs["json"]["chat_id"] == "@chan"

    def test_send_http_error_returns_false(self):
        n = _make_notifier(cooldown=0.0)
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request"

        with patch("requests.post", return_value=mock_resp):
            result = n.send("test")

        assert result is False

    def test_send_network_error_returns_false(self):
        n = _make_notifier(cooldown=0.0)
        with patch("requests.post", side_effect=ConnectionError("unreachable")):
            result = n.send("test")
        assert result is False

    def test_cooldown_blocks_second_send(self):
        n = _make_notifier(cooldown=60.0)
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("requests.post", return_value=mock_resp) as mock_post:
            r1 = n.send("first", alert_key="x")
            r2 = n.send("second", alert_key="x")  # même clé → cooldown

        assert r1 is True
        assert r2 is False
        assert mock_post.call_count == 1

    def test_different_keys_not_blocked(self):
        n = _make_notifier(cooldown=60.0)
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("requests.post", return_value=mock_resp) as mock_post:
            r1 = n.send("signal", alert_key="buy")
            r2 = n.send("whale", alert_key="whale")

        assert r1 is True
        assert r2 is True
        assert mock_post.call_count == 2


class TestTelegramNotifierSignals:
    def test_send_signal_buy(self):
        n = _make_notifier(cooldown=0.0)
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = n.send_signal("BUY", "BTCUSDT", 60000.0)

        assert result is True
        text = mock_post.call_args.kwargs["json"]["text"]
        assert "BUY" in text
        assert "BTCUSDT" in text

    def test_send_signal_hold_skipped(self):
        n = _make_notifier(cooldown=0.0)
        with patch("requests.post") as mock_post:
            result = n.send_signal("HOLD", "BTCUSDT", 60000.0)
        assert result is False
        mock_post.assert_not_called()

    def test_send_whale_alert_empty_list(self):
        n = _make_notifier(cooldown=0.0)
        with patch("requests.post") as mock_post:
            result = n.send_whale_alert([])
        assert result is False
        mock_post.assert_not_called()

    def test_send_whale_alert_with_alerts(self):
        n = _make_notifier(cooldown=0.0)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.post", return_value=mock_resp):
            result = n.send_whale_alert(["Whale BTC 2M$", "Whale ETH 1M$"])
        assert result is True

    def test_send_health_alert_above_50_skipped(self):
        n = _make_notifier(cooldown=0.0)
        with patch("requests.post") as mock_post:
            result = n.send_health_alert(75.0)
        assert result is False
        mock_post.assert_not_called()

    def test_send_health_alert_below_50(self):
        n = _make_notifier(cooldown=0.0)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.post", return_value=mock_resp):
            result = n.send_health_alert(30.0, "Réduire drawdown")
        assert result is True


# ===========================================================================
# Tests BacktestLab data_mode (option J)
# ===========================================================================


def _make_candles(closes: list[float]) -> list[dict]:
    return [
        {"symbol": "BTCUSDT", "timestamp": f"2024-01-{i+1:02d}",
         "open": c, "high": c * 1.01, "low": c * 0.99, "close": c, "volume": 100.0}
        for i, c in enumerate(closes)
    ]


class TestBacktestDataMode:
    def test_real_data_mode_with_multiple_candles(self):
        lab = BacktestLab()
        candles = _make_candles([60_000, 61_000, 62_000, 63_000])
        strategy = {"entry_indicator": "EMA", "threshold": 0.5}
        result = lab.run_backtest(strategy, candles)
        assert result["data_mode"] == "real"

    def test_synthetic_data_mode_with_one_candle(self):
        lab = BacktestLab()
        candles = _make_candles([60_000])
        strategy = {"entry_indicator": "EMA", "threshold": 0.5}
        result = lab.run_backtest(strategy, candles)
        assert result["data_mode"] == "synthetic"

    def test_synthetic_data_mode_with_empty_list(self):
        lab = BacktestLab()
        strategy = {"entry_indicator": "RSI", "threshold": 0.5}
        result = lab.run_backtest(strategy, [])
        assert result["data_mode"] == "synthetic"

    def test_candles_count_in_result(self):
        lab = BacktestLab()
        candles = _make_candles([60_000, 61_000, 62_000])
        strategy = {"entry_indicator": "EMA", "threshold": 0.5}
        result = lab.run_backtest(strategy, candles)
        assert result["candles_count"] == 3


# ===========================================================================
# Tests DirectorDashboard backtest_summary (option J)
# ===========================================================================


class TestDirectorBacktestSummary:
    def test_update_accepts_backtest_summary(self):
        from dashboard.director_dashboard import DirectorDashboard
        d = DirectorDashboard()
        snap = d.update(
            cycle=1,
            backtest_summary={
                "strategy_count": 10,
                "best_pnl": 5.2,
                "best_sharpe": 1.8,
                "max_drawdown": 0.05,
                "data_mode": "real",
                "candles_count": 200,
            },
        )
        assert snap.backtest_summary["data_mode"] == "real"
        assert snap.backtest_summary["best_pnl"] == pytest.approx(5.2)

    def test_render_contains_backtest_section(self):
        from dashboard.director_dashboard import DirectorDashboard
        d = DirectorDashboard()
        snap = d.update(
            cycle=1,
            backtest_summary={
                "strategy_count": 5,
                "best_pnl": 3.0,
                "best_sharpe": 1.2,
                "max_drawdown": 0.03,
                "data_mode": "real",
                "candles_count": 100,
            },
        )
        report = d.render(snap)
        assert "BACKTEST REPORT" in report
        assert "REAL" in report
        assert "100" in report

    def test_render_no_backtest_section_when_empty(self):
        from dashboard.director_dashboard import DirectorDashboard
        d = DirectorDashboard()
        snap = d.update(cycle=1)
        report = d.render(snap)
        assert "BACKTEST REPORT" not in report
