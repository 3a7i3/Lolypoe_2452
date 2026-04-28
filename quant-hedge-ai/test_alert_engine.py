"""
Tests option AF — Moteur d'alertes Slack/Discord.

Tout est mocké (urllib.request.urlopen) — aucun appel réseau réel.
"""
from __future__ import annotations

import json
import time
import threading
from unittest.mock import MagicMock, patch, call
import urllib.error

import pytest

from agents.alerts.alert_engine import Alert, AlertEngine, AlertLevel


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_ok_response() -> MagicMock:
    """Simule une réponse HTTP 200."""
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=ctx)
    ctx.__exit__ = MagicMock(return_value=False)
    ctx.status = 200
    return ctx


def _engine(**kwargs) -> AlertEngine:
    """Crée un AlertEngine configuré pour les tests."""
    defaults = dict(
        slack_url="https://hooks.slack.com/test",
        discord_url="https://discord.com/api/webhooks/test",
        cooldown_s=0,  # pas de cooldown en test
        enabled=True,
        http_timeout_s=1.0,
        max_retries=1,
    )
    defaults.update(kwargs)
    return AlertEngine(**defaults)


def _wait_queue_empty(engine: AlertEngine, timeout_s: float = 3.0) -> None:
    engine.flush(timeout_s=timeout_s)


# ── Tests Alert dataclass ─────────────────────────────────────────────────────

class TestAlertDataclass:
    def test_default_level_is_info(self) -> None:
        a = Alert(title="T", message="M")
        assert a.level == AlertLevel.INFO

    def test_fields_optional(self) -> None:
        a = Alert(title="T", message="M", level=AlertLevel.CRITICAL)
        assert a.fields == {}

    def test_timestamp_auto(self) -> None:
        before = time.time()
        a = Alert(title="T", message="M")
        assert a.timestamp >= before


# ── Tests init & activation ───────────────────────────────────────────────────

class TestAlertEngineInit:
    def test_disabled_engine_does_not_enqueue(self) -> None:
        e = AlertEngine(enabled=False, slack_url="https://hooks.slack.com/x")
        with patch("urllib.request.urlopen") as mock_open:
            e.send(Alert(title="T", message="M"))
            _wait_queue_empty(e)
            mock_open.assert_not_called()

    def test_no_urls_does_not_call_http(self) -> None:
        e = AlertEngine(slack_url="", discord_url="", enabled=True)
        with patch("urllib.request.urlopen") as mock_open:
            e.send(Alert(title="T", message="M"))
            _wait_queue_empty(e)
            mock_open.assert_not_called()

    def test_worker_thread_is_daemon(self) -> None:
        e = AlertEngine()
        assert e._worker.daemon is True


# ── Tests envoi Slack ─────────────────────────────────────────────────────────

class TestSlackPayload:
    def test_slack_payload_structure(self) -> None:
        e = AlertEngine(slack_url="https://hooks.slack.com/x", discord_url="", cooldown_s=0)
        a = Alert(title="Test", message="Msg", level=AlertLevel.WARNING, fields={"k": "v"})
        payload = e._build_slack_payload(a)
        assert "attachments" in payload
        att = payload["attachments"][0]
        assert att["title"] == "Test"
        assert att["text"] == "Msg"
        assert len(att["fields"]) == 1
        assert att["fields"][0]["title"] == "k"

    def test_slack_color_critical(self) -> None:
        e = AlertEngine()
        a = Alert(title="T", message="M", level=AlertLevel.CRITICAL)
        payload = e._build_slack_payload(a)
        assert payload["attachments"][0]["color"] == "#E94560"

    def test_slack_color_info(self) -> None:
        e = AlertEngine()
        a = Alert(title="T", message="M", level=AlertLevel.INFO)
        payload = e._build_slack_payload(a)
        assert payload["attachments"][0]["color"] == "#00D4AA"

    def test_slack_http_post_called(self) -> None:
        e = _engine(discord_url="")
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.send(Alert(title="T", message="M"))
            _wait_queue_empty(e)
            assert mock_open.called
            req = mock_open.call_args[0][0]
            assert "hooks.slack.com" in req.full_url


# ── Tests envoi Discord ───────────────────────────────────────────────────────

class TestDiscordPayload:
    def test_discord_payload_structure(self) -> None:
        e = AlertEngine(discord_url="https://discord.com/api/webhooks/x", cooldown_s=0)
        a = Alert(title="T", message="M", level=AlertLevel.INFO, fields={"Cycle": "5"})
        payload = e._build_discord_payload(a)
        assert "embeds" in payload
        embed = payload["embeds"][0]
        assert embed["title"] == "T"
        assert embed["color"] == 0x00D4AA
        assert embed["fields"][0]["name"] == "Cycle"

    def test_discord_http_post_called(self) -> None:
        e = _engine(slack_url="")
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.send(Alert(title="T", message="M"))
            _wait_queue_empty(e)
            req = mock_open.call_args[0][0]
            assert "discord.com" in req.full_url

    def test_both_urls_calls_http_twice(self) -> None:
        e = _engine()
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.send(Alert(title="T", message="M"))
            _wait_queue_empty(e)
            assert mock_open.call_count == 2


# ── Tests retry / erreur réseau ───────────────────────────────────────────────

class TestHttpRetry:
    def test_url_error_does_not_raise(self) -> None:
        e = _engine(discord_url="", max_retries=2)
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            e.send(Alert(title="T", message="M"))
            _wait_queue_empty(e)
            # Pas d'exception propagée

    def test_http_500_retries(self) -> None:
        bad_resp = _mock_ok_response()
        bad_resp.status = 500
        e = _engine(discord_url="", max_retries=2)
        with patch("urllib.request.urlopen", return_value=bad_resp) as mock_open:
            e.send(Alert(title="T", message="M"))
            _wait_queue_empty(e)
            assert mock_open.call_count == 2  # 2 tentatives


# ── Tests cooldown anti-spam ──────────────────────────────────────────────────

class TestCooldown:
    def test_cooldown_blocks_second_send(self) -> None:
        e = _engine(cooldown_s=3600)
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.maybe_alert_drawdown(cycle=1, drawdown_pct=12.0, equity=90_000.0)
            e.maybe_alert_drawdown(cycle=2, drawdown_pct=13.0, equity=89_000.0)
            _wait_queue_empty(e)
            assert mock_open.call_count == 2  # Slack + Discord (1 alerte × 2 endpoints)

    def test_cooldown_zero_allows_every_call(self) -> None:
        e = _engine(cooldown_s=0)
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.maybe_alert_drawdown(cycle=1, drawdown_pct=12.0, equity=90_000.0)
            e.maybe_alert_drawdown(cycle=2, drawdown_pct=13.0, equity=89_000.0)
            _wait_queue_empty(e)
            assert mock_open.call_count == 4  # 2 alertes × 2 endpoints

    def test_cooldown_expired_sends_again(self) -> None:
        e = _engine(cooldown_s=0)
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()):
            e._mark_sent("drawdown_critical")
            # cooldown_s=0 → toujours expiré
            assert e._cooldown_expired("drawdown_critical")


# ── Tests maybe_alert_drawdown ────────────────────────────────────────────────

class TestMaybeAlertDrawdown:
    def test_below_warning_returns_false(self) -> None:
        e = _engine()
        assert e.maybe_alert_drawdown(cycle=1, drawdown_pct=2.0, equity=100_000.0) is False

    def test_warning_level_returns_true(self) -> None:
        e = _engine()
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()):
            result = e.maybe_alert_drawdown(cycle=1, drawdown_pct=7.0, equity=93_000.0)
            _wait_queue_empty(e)
        assert result is True

    def test_critical_level_returns_true(self) -> None:
        e = _engine()
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()):
            result = e.maybe_alert_drawdown(cycle=1, drawdown_pct=12.0, equity=88_000.0)
            _wait_queue_empty(e)
        assert result is True

    def test_same_level_blocked_by_cooldown(self) -> None:
        e = _engine(cooldown_s=3600)
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.maybe_alert_drawdown(cycle=1, drawdown_pct=12.0, equity=88_000.0)
            result2 = e.maybe_alert_drawdown(cycle=2, drawdown_pct=13.0, equity=87_000.0)
            _wait_queue_empty(e)
        assert result2 is False

    def test_reset_when_below_warning(self) -> None:
        e = _engine(cooldown_s=0)
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()):
            e.maybe_alert_drawdown(cycle=1, drawdown_pct=12.0, equity=88_000.0)
            e.maybe_alert_drawdown(cycle=2, drawdown_pct=1.0, equity=99_000.0)  # reset
            result = e.maybe_alert_drawdown(cycle=3, drawdown_pct=12.0, equity=88_000.0)
            _wait_queue_empty(e)
        assert result is True


# ── Tests maybe_alert_circuit_breaker ────────────────────────────────────────

class TestMaybeAlertCircuitBreaker:
    def test_sends_critical_alert(self) -> None:
        e = _engine()
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            result = e.maybe_alert_circuit_breaker(cycle=5, reason="drawdown limite", equity=85_000.0)
            _wait_queue_empty(e)
        assert result is True
        assert mock_open.called

    def test_cooldown_blocks_repeat(self) -> None:
        e = _engine(cooldown_s=3600)
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.maybe_alert_circuit_breaker(cycle=5, reason="R", equity=85_000.0)
            result2 = e.maybe_alert_circuit_breaker(cycle=6, reason="R", equity=84_000.0)
            _wait_queue_empty(e)
        assert result2 is False


# ── Tests maybe_alert_new_best_strategy ──────────────────────────────────────

class TestMaybeAlertNewBest:
    def test_significant_improvement_sends(self) -> None:
        e = _engine(cooldown_s=0)
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()):
            result = e.maybe_alert_new_best_strategy(cycle=3, strategy_type="MACD→EMA", sharpe=3.5)
            _wait_queue_empty(e)
        assert result is True
        assert e._best_sharpe_seen == pytest.approx(3.5)

    def test_minor_improvement_ignored(self) -> None:
        e = _engine(cooldown_s=0, sharpe_improvement_threshold=1.0)
        e._best_sharpe_seen = 3.0
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()):
            result = e.maybe_alert_new_best_strategy(cycle=4, strategy_type="EMA", sharpe=3.4)
        assert result is False


# ── Tests alertes informatives ────────────────────────────────────────────────

class TestInfoAlerts:
    def test_loop_finished_sends(self) -> None:
        e = _engine()
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.alert_loop_finished(total_cycles=10, equity=110_000.0, pnl=10_000.0, best_sharpe=4.2)
            _wait_queue_empty(e)
        assert mock_open.called

    def test_loop_paused_sends(self) -> None:
        e = _engine()
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.alert_loop_paused(cycle=7)
            _wait_queue_empty(e)
        assert mock_open.called

    def test_loop_resumed_sends(self) -> None:
        e = _engine()
        with patch("urllib.request.urlopen", return_value=_mock_ok_response()) as mock_open:
            e.alert_loop_resumed(cycle=8)
            _wait_queue_empty(e)
        assert mock_open.called


# ── Tests RuntimeConfig champs AF ─────────────────────────────────────────────

class TestAFRuntimeConfig:
    def test_alerts_fields_exist(self) -> None:
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert hasattr(cfg, "alerts_enabled")
        assert hasattr(cfg, "alerts_slack_url")
        assert hasattr(cfg, "alerts_discord_url")
        assert hasattr(cfg, "alerts_cooldown_s")
        assert hasattr(cfg, "alerts_drawdown_warning_pct")
        assert hasattr(cfg, "alerts_drawdown_critical_pct")
        assert hasattr(cfg, "alerts_sharpe_improvement")

    def test_alerts_defaults(self) -> None:
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert cfg.alerts_enabled is False
        assert cfg.alerts_slack_url == ""
        assert cfg.alerts_discord_url == ""
        assert cfg.alerts_cooldown_s == 300
        assert cfg.alerts_drawdown_warning_pct == pytest.approx(5.0)
        assert cfg.alerts_drawdown_critical_pct == pytest.approx(10.0)
        assert cfg.alerts_sharpe_improvement == pytest.approx(0.5)

    def test_alerts_env_parsing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from runtime_config import load_runtime_config_from_env
        monkeypatch.setenv("V9_ALERTS_ENABLED", "true")
        monkeypatch.setenv("V9_ALERTS_SLACK_URL", "https://hooks.slack.com/env-test")
        monkeypatch.setenv("V9_ALERTS_COOLDOWN_S", "60")
        monkeypatch.setenv("V9_ALERTS_DD_WARNING", "3.5")
        monkeypatch.setenv("V9_ALERTS_DD_CRITICAL", "8.0")
        monkeypatch.setenv("V9_ALERTS_SHARPE_IMPROVE", "1.0")
        cfg = load_runtime_config_from_env()
        assert cfg.alerts_enabled is True
        assert cfg.alerts_slack_url == "https://hooks.slack.com/env-test"
        assert cfg.alerts_cooldown_s == 60
        assert cfg.alerts_drawdown_warning_pct == pytest.approx(3.5)
        assert cfg.alerts_drawdown_critical_pct == pytest.approx(8.0)
        assert cfg.alerts_sharpe_improvement == pytest.approx(1.0)

    def test_alerts_in_as_dict(self) -> None:
        from runtime_config import RuntimeConfig
        d = RuntimeConfig().as_dict()
        assert "alerts_enabled" in d
        assert "alerts_slack_url" in d
        assert "alerts_cooldown_s" in d


# ── Tests thread-safety ───────────────────────────────────────────────────────

class TestThreadSafety:
    def test_concurrent_sends_no_crash(self) -> None:
        e = _engine(cooldown_s=0)
        errors: list[Exception] = []

        def spam_alerts(n: int) -> None:
            try:
                with patch("urllib.request.urlopen", return_value=_mock_ok_response()):
                    for i in range(n):
                        e.maybe_alert_drawdown(cycle=i, drawdown_pct=12.0, equity=88_000.0)
            except Exception as ex:
                errors.append(ex)

        threads = [threading.Thread(target=spam_alerts, args=(10,)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        _wait_queue_empty(e)
        assert not errors

    def test_queue_full_drops_alert(self) -> None:
        e = AlertEngine(
            slack_url="https://hooks.slack.com/x",
            enabled=True,
            max_queue_size=1,
            cooldown_s=0,
        )
        # Bloquer le worker pour saturer la queue
        with patch("urllib.request.urlopen", side_effect=lambda *a, **kw: time.sleep(5)):
            e.send(Alert(title="T1", message="M"))
            e.send(Alert(title="T2", message="M"))  # doit être ignorée silencieusement
