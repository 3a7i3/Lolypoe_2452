"""
Tests — Option AL : EmailNotifier SMTP.
"""
from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch, call

import pytest

from agents.alerts.email_notifier import EmailConfig, EmailNotifier, _LEVEL_COLOR, _LEVEL_EMOJI


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def dry_config() -> EmailConfig:
    return EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        username="bot@gmail.com",
        password="secret",
        from_addr="bot@gmail.com",
        to_addrs=["trader@example.com"],
        dry_run=True,
    )


@pytest.fixture
def dry_notifier(dry_config) -> EmailNotifier:
    return EmailNotifier(dry_config)


@pytest.fixture
def unconfigured_notifier() -> EmailNotifier:
    return EmailNotifier(EmailConfig())  # tous les champs vides


# ── Tests EmailConfig ─────────────────────────────────────────────────────────

def test_config_defaults():
    cfg = EmailConfig()
    assert cfg.smtp_host == "smtp.gmail.com"
    assert cfg.smtp_port == 587
    assert cfg.use_tls is True
    assert cfg.dry_run is False
    assert cfg.timeout_s == 10.0
    assert cfg.to_addrs == []


def test_config_ssl_port():
    cfg = EmailConfig(smtp_port=465, use_tls=False)
    assert cfg.smtp_port == 465
    assert cfg.use_tls is False


# ── Tests is_configured ───────────────────────────────────────────────────────

def test_is_configured_true(dry_notifier):
    assert dry_notifier.is_configured() is True


def test_is_configured_false_no_host():
    n = EmailNotifier(EmailConfig(smtp_host="", username="u", from_addr="f", to_addrs=["t"]))
    assert n.is_configured() is False


def test_is_configured_false_no_username():
    n = EmailNotifier(EmailConfig(smtp_host="h", username="", from_addr="f", to_addrs=["t"]))
    assert n.is_configured() is False


def test_is_configured_false_no_from():
    n = EmailNotifier(EmailConfig(smtp_host="h", username="u", from_addr="", to_addrs=["t"]))
    assert n.is_configured() is False


def test_is_configured_false_no_to():
    n = EmailNotifier(EmailConfig(smtp_host="h", username="u", from_addr="f", to_addrs=[]))
    assert n.is_configured() is False


def test_unconfigured_returns_false(unconfigured_notifier):
    assert unconfigured_notifier.is_configured() is False


# ── Tests dry_run ─────────────────────────────────────────────────────────────

def test_dry_run_returns_true(dry_notifier):
    result = dry_notifier.send_alert("Test", "Contenu")
    assert result is True


def test_dry_run_no_smtp_call(dry_notifier):
    with patch("smtplib.SMTP") as mock_smtp:
        dry_notifier.send_alert("Test", "Corps")
        mock_smtp.assert_not_called()


def test_dry_run_logs(dry_notifier, caplog):
    with caplog.at_level(logging.INFO, logger="agents.alerts.email_notifier"):
        dry_notifier.send_alert("Test", "Corps")
    assert any("dry-run" in r.message for r in caplog.records)


def test_dry_run_summary(dry_notifier):
    result = dry_notifier.send_summary(
        total_cycles=10,
        equity=105_000.0,
        pnl=5_000.0,
        best_sharpe=1.5,
    )
    assert result is True


# ── Tests unconfigured ────────────────────────────────────────────────────────

def test_unconfigured_returns_false_on_send(unconfigured_notifier):
    result = unconfigured_notifier.send_alert("Test", "Corps")
    assert result is False


# ── Tests _build_html ─────────────────────────────────────────────────────────

def test_build_html_contains_title(dry_notifier):
    html = dry_notifier._build_html("Mon Titre", "Corps", "info", {})
    assert "Mon Titre" in html


def test_build_html_contains_body(dry_notifier):
    html = dry_notifier._build_html("T", "Corps spécial", "info", {})
    assert "Corps spécial" in html


def test_build_html_correct_color_info(dry_notifier):
    html = dry_notifier._build_html("T", "B", "info", {})
    assert _LEVEL_COLOR["info"] in html


def test_build_html_correct_color_warning(dry_notifier):
    html = dry_notifier._build_html("T", "B", "warning", {})
    assert _LEVEL_COLOR["warning"] in html


def test_build_html_correct_color_critical(dry_notifier):
    html = dry_notifier._build_html("T", "B", "critical", {})
    assert _LEVEL_COLOR["critical"] in html


def test_build_html_contains_emoji(dry_notifier):
    html = dry_notifier._build_html("T", "B", "warning", {})
    assert _LEVEL_EMOJI["warning"] in html


def test_build_html_with_fields(dry_notifier):
    html = dry_notifier._build_html("T", "B", "info", {"Clé": "Valeur"})
    assert "Clé" in html
    assert "Valeur" in html


def test_build_html_without_fields(dry_notifier):
    html = dry_notifier._build_html("T", "B", "info", {})
    assert "<table" not in html


def test_build_html_unknown_level_no_crash(dry_notifier):
    html = dry_notifier._build_html("T", "B", "unknown_level", {})
    assert "T" in html


# ── Tests send_alert niveaux ──────────────────────────────────────────────────

def test_send_alert_all_levels(dry_notifier):
    for level in ("info", "warning", "critical"):
        result = dry_notifier.send_alert("Titre", "Corps", level=level)
        assert result is True


def test_send_alert_with_fields(dry_notifier):
    result = dry_notifier.send_alert(
        "Alerte", "Message", "info", fields={"Cycle": "42", "Equity": "$100k"}
    )
    assert result is True


# ── Tests subject format ──────────────────────────────────────────────────────

def test_subject_contains_title(dry_notifier, caplog):
    with caplog.at_level(logging.INFO, logger="agents.alerts.email_notifier"):
        dry_notifier.send_alert("Mon Titre Important", "Corps")
    assert any("Mon Titre Important" in r.message for r in caplog.records)


# ── Tests attach_to_alert_engine ─────────────────────────────────────────────

def _make_mock_alert(level_str: str = "info") -> MagicMock:
    alert = MagicMock()
    level = MagicMock()
    level.value = level_str
    alert.level = level
    alert.title = "Test Alert"
    alert.message = "Test message"
    alert.fields = {"k": "v"}
    return alert


def test_attach_patches_dispatch(dry_notifier):
    engine = MagicMock()
    original = engine._dispatch
    dry_notifier.attach_to_alert_engine(engine)
    assert engine._dispatch is not original


def test_attach_calls_original_dispatch(dry_notifier):
    engine = MagicMock()
    original_dispatch = MagicMock()
    engine._dispatch = original_dispatch

    dry_notifier.attach_to_alert_engine(engine)

    alert = _make_mock_alert("warning")
    engine._dispatch(alert)
    original_dispatch.assert_called_once_with(alert)


def test_attach_sends_email_on_dispatch(dry_notifier):
    engine = MagicMock()
    engine._dispatch = MagicMock()

    with patch.object(dry_notifier, "send_alert", return_value=True) as mock_send:
        dry_notifier.attach_to_alert_engine(engine)
        alert = _make_mock_alert("critical")
        engine._dispatch(alert)
        mock_send.assert_called_once_with(
            title=alert.title,
            body=alert.message,
            level="critical",
            fields=alert.fields,
        )


def test_attach_level_from_string(dry_notifier):
    """Level sans .value (string directe)."""
    engine = MagicMock()
    engine._dispatch = MagicMock()

    with patch.object(dry_notifier, "send_alert", return_value=True) as mock_send:
        dry_notifier.attach_to_alert_engine(engine)
        alert = MagicMock()
        alert.level = "info"  # pas d'attribut .value
        alert.title = "T"
        alert.message = "M"
        alert.fields = {}
        engine._dispatch(alert)
        mock_send.assert_called_once()
        _, kwargs = mock_send.call_args
        assert kwargs["level"] == "info"


# ── Tests send_summary ────────────────────────────────────────────────────────

def test_send_summary_fields(dry_notifier):
    result = dry_notifier.send_summary(
        total_cycles=25,
        equity=120_000.0,
        pnl=20_000.0,
        best_sharpe=2.5,
    )
    assert result is True


# ── Tests SMTP réel (mocké) ───────────────────────────────────────────────────

def test_smtp_starttls_called():
    cfg = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="u",
        password="p",
        from_addr="f@example.com",
        to_addrs=["t@example.com"],
        use_tls=True,
        dry_run=False,
    )
    notifier = EmailNotifier(cfg)

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)

    with patch("smtplib.SMTP", return_value=mock_smtp_instance):
        result = notifier.send_alert("T", "B")

    assert result is True
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("u", "p")
    mock_smtp_instance.sendmail.assert_called_once()


def test_smtp_ssl_called():
    cfg = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=465,
        username="u",
        password="p",
        from_addr="f@example.com",
        to_addrs=["t@example.com"],
        use_tls=False,
        dry_run=False,
    )
    notifier = EmailNotifier(cfg)

    mock_ssl_instance = MagicMock()
    mock_ssl_instance.__enter__ = MagicMock(return_value=mock_ssl_instance)
    mock_ssl_instance.__exit__ = MagicMock(return_value=False)

    with patch("smtplib.SMTP_SSL", return_value=mock_ssl_instance):
        result = notifier.send_alert("T", "B")

    assert result is True
    mock_ssl_instance.login.assert_called_once_with("u", "p")
    mock_ssl_instance.sendmail.assert_called_once()


def test_smtp_failure_returns_false():
    import smtplib
    cfg = EmailConfig(
        smtp_host="bad.host",
        smtp_port=587,
        username="u",
        password="p",
        from_addr="f@bad.host",
        to_addrs=["t@bad.host"],
        dry_run=False,
    )
    notifier = EmailNotifier(cfg)

    with patch("smtplib.SMTP", side_effect=smtplib.SMTPException("connexion refusée")):
        with patch("time.sleep"):  # éviter l'attente réelle
            result = notifier.send_alert("T", "B")

    assert result is False
