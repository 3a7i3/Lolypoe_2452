from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from strategy_factory import StrategyFactory
from strategy_factory.bot_doctor_validator import BotDoctorValidator
from ai_evolution import StrategyMemoryStore


def _sample_candles() -> list[dict]:
    return [
        {"symbol": "BTCUSDT", "timestamp": "2026-01-01T00:00:00Z", "open": 50000, "close": 50200, "high": 50300, "low": 49800, "volume": 120000},
        {"symbol": "ETHUSDT", "timestamp": "2026-01-01T00:00:00Z", "open": 3000, "close": 3020, "high": 3050, "low": 2960, "volume": 85000},
        {"symbol": "SOLUSDT", "timestamp": "2026-01-01T00:00:00Z", "open": 120, "close": 123, "high": 125, "low": 118, "volume": 64000},
    ]


def test_validator_blocks_bad_strategy() -> None:
    validator = BotDoctorValidator()
    decision = validator.validate({"sharpe": 0.2, "drawdown": 0.25, "win_rate": 0.2, "pnl": -40})
    assert decision.approved is False
    assert decision.health_score < 50


def test_validator_approves_good_strategy() -> None:
    validator = BotDoctorValidator()
    decision = validator.validate({"sharpe": 2.8, "drawdown": 0.04, "win_rate": 0.62, "pnl": 25})
    assert decision.approved is True
    assert decision.health_score >= 50


def test_factory_run() -> None:
    factory = StrategyFactory()
    report = factory.run(_sample_candles(), target_count=40, generations=1, regime="bull_trend")
    assert report.generated_count > 0
    assert report.backtested_count == report.generated_count
    assert report.filtered_count <= report.backtested_count
    assert report.approved_count + report.blocked_count == report.filtered_count
    assert report.regime == "bull_trend"
    assert report.regime_stability >= 0
    assert report.memory_loaded_count >= 0
    assert report.memory_saved_count >= 0
    assert report.avg_loaded_age_cycles >= 0


def test_factory_report_dict() -> None:
    factory = StrategyFactory()
    report = factory.run(_sample_candles(), target_count=30, generations=1, regime="sideways")
    payload = report.as_dict()
    assert "approved_count" in payload
    assert "blocked_count" in payload
    assert "top_strategies" in payload
    assert "regime" in payload
    assert "regime_stability" in payload
    assert "memory_loaded_count" in payload
    assert "memory_saved_count" in payload
    assert "avg_loaded_age_cycles" in payload


def test_memory_store_tracks_stability() -> None:
    store = StrategyMemoryStore()
    store.save_for_regime("trend", [])
    store.save_for_regime("trend", [])
    store.save_for_regime("trend", [])
    stability = store.get_regime_stability("trend")
    assert stability > 0


def test_memory_ranking_penalizes_overuse() -> None:
    rows = [
        {
            "strategy": {"name": "fresh"},
            "sharpe": 2.0,
            "drawdown": 0.05,
            "win_rate": 0.6,
            "pnl": 20.0,
            "freshness": 1.0,
            "usage_count": 0,
        },
        {
            "strategy": {"name": "overused"},
            "sharpe": 2.0,
            "drawdown": 0.05,
            "win_rate": 0.6,
            "pnl": 20.0,
            "freshness": 1.0,
            "usage_count": 20,
        },
    ]
    ranked = StrategyMemoryStore._rank_for_loading(rows, regime_stability=1.0)
    assert ranked[0]["strategy"]["name"] == "fresh"


if __name__ == "__main__":
    tests = [
        ("validator_blocks_bad_strategy", test_validator_blocks_bad_strategy),
        ("validator_approves_good_strategy", test_validator_approves_good_strategy),
        ("factory_run", test_factory_run),
        ("factory_report_dict", test_factory_report_dict),
        ("memory_store_tracks_stability", test_memory_store_tracks_stability),
        ("memory_ranking_penalizes_overuse", test_memory_ranking_penalizes_overuse),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {name}: {exc}")
            failed += 1
    print(f"Results: {passed} passed, {failed} failed")
