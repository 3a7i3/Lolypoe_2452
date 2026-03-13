from __future__ import annotations

import os

from main_v91 import _get_env_int
from runtime_config import get_env_bool, get_env_float, get_env_str, load_runtime_config_from_env



def test_get_env_int_returns_default_when_missing() -> None:
    os.environ.pop("V9_TEST_INT", None)
    assert _get_env_int("V9_TEST_INT", 7) == 7



def test_get_env_int_returns_default_on_invalid_value() -> None:
    os.environ["V9_TEST_INT"] = "abc"
    assert _get_env_int("V9_TEST_INT", 11) == 11



def test_get_env_int_applies_min_value() -> None:
    os.environ["V9_TEST_INT"] = "-5"
    assert _get_env_int("V9_TEST_INT", 3, min_value=0) == 0



def test_get_env_int_parses_valid_integer() -> None:
    os.environ["V9_TEST_INT"] = "42"
    assert _get_env_int("V9_TEST_INT", 3, min_value=0) == 42


def test_get_env_float_returns_default_on_invalid_value() -> None:
    os.environ["V9_TEST_FLOAT"] = "not-a-float"
    assert get_env_float("V9_TEST_FLOAT", 0.5, min_value=0.0, max_value=1.0) == 0.5


def test_get_env_float_applies_bounds() -> None:
    os.environ["V9_TEST_FLOAT"] = "9.9"
    assert get_env_float("V9_TEST_FLOAT", 0.5, min_value=0.0, max_value=1.0) == 1.0


def test_get_env_bool_parsing() -> None:
    os.environ["V9_TEST_BOOL"] = "yes"
    assert get_env_bool("V9_TEST_BOOL", False) is True

    os.environ["V9_TEST_BOOL"] = "off"
    assert get_env_bool("V9_TEST_BOOL", True) is False


def test_get_env_bool_invalid_falls_back_to_default() -> None:
    os.environ["V9_TEST_BOOL"] = "maybe"
    assert get_env_bool("V9_TEST_BOOL", True) is True


def test_get_env_str_returns_trimmed_value_or_default() -> None:
    os.environ["V9_TEST_STR"] = "  user-42  "
    assert get_env_str("V9_TEST_STR", "fallback") == "user-42"

    os.environ["V9_TEST_STR"] = "   "
    assert get_env_str("V9_TEST_STR", "fallback") == "fallback"


def test_runtime_config_loads_new_decision_parameters() -> None:
    os.environ["V9_MIN_SHARPE"] = "2.8"
    os.environ["V9_TRADE_MAX_DRAWDOWN"] = "0.12"
    os.environ["V9_WHALE_BLOCK_THRESHOLD"] = "4"
    os.environ["V9_MAX_RISK_PER_TRADE"] = "0.03"

    cfg = load_runtime_config_from_env()

    assert cfg.min_sharpe_for_trade == 2.8
    assert cfg.trade_max_drawdown == 0.12
    assert cfg.whale_block_threshold == 4
    assert cfg.max_risk_per_trade == 0.03


def test_runtime_config_clamps_new_decision_parameters() -> None:
    os.environ["V9_MIN_SHARPE"] = "-5"
    os.environ["V9_TRADE_MAX_DRAWDOWN"] = "5"
    os.environ["V9_WHALE_BLOCK_THRESHOLD"] = "-1"
    os.environ["V9_MAX_RISK_PER_TRADE"] = "0"

    cfg = load_runtime_config_from_env()

    assert cfg.min_sharpe_for_trade == 0.0
    assert cfg.trade_max_drawdown == 1.0
    assert cfg.whale_block_threshold == 0
    assert cfg.max_risk_per_trade == 0.001


def test_runtime_config_loads_doctor_telegram_settings() -> None:
    os.environ["V9_DOCTOR_TELEGRAM_ENABLED"] = "true"
    os.environ["V9_DOCTOR_TELEGRAM_USER_ID"] = "  12345  "
    os.environ["V9_DOCTOR_V26_REPORT_ENABLED"] = "yes"
    os.environ["V9_DOCTOR_REPORT_EXPORT_ENABLED"] = "1"
    os.environ["V9_DOCTOR_REPORT_EXPORT_DIR"] = "  databases/custom_doctor_reports  "

    cfg = load_runtime_config_from_env()

    assert cfg.doctor_telegram_enabled is True
    assert cfg.doctor_telegram_user_id == "12345"
    assert cfg.doctor_v26_report_enabled is True
    assert cfg.doctor_report_export_enabled is True
    assert cfg.doctor_report_export_dir == "databases/custom_doctor_reports"
