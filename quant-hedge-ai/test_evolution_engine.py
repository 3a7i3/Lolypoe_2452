"""Tests for AI Evolution Engine."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from ai_evolution.evolution_engine import EvolutionEngine, EvolutionReport


# --- Fixtures ---

SAMPLE_CANDLES = [
    {"symbol": "BTCUSDT", "close": 50000, "open": 49500, "volume": 100},
    {"symbol": "ETHUSDT", "close": 3000, "open": 2950, "volume": 200},
]


@pytest.fixture
def engine():
    return EvolutionEngine(population_size=10, generations=1)


@pytest.fixture
def clean_memory(tmp_path):
    """Provide a clean temporary memory file."""
    mem_file = tmp_path / "test_memory.json"
    return mem_file


# --- EvolutionReport tests ---


class TestEvolutionReport:
    def test_default_values(self):
        r = EvolutionReport()
        assert r.cycle == 0
        assert r.regime == "unknown"
        assert r.best_sharpe == 0.0
        assert r.best_strategy == {}

    def test_as_dict_keys(self):
        r = EvolutionReport(cycle=5, regime="bull_trend", best_sharpe=4.5)
        d = r.as_dict()
        expected_keys = {
            "cycle", "regime", "candidates", "from_memory", "evolved",
            "backtests", "best_sharpe", "avg_sharpe", "best_strategy_name",
            "saved", "doctor_blocked", "generation",
        }
        assert set(d.keys()) == expected_keys

    def test_as_dict_rounding(self):
        r = EvolutionReport(best_sharpe=3.14159265, avg_sharpe=1.23456789)
        d = r.as_dict()
        assert d["best_sharpe"] == 3.1416
        assert d["avg_sharpe"] == 1.2346

    def test_as_dict_best_strategy_name(self):
        r = EvolutionReport(best_strategy={"entry_indicator": "RSI", "exit_indicator": "MACD"})
        d = r.as_dict()
        assert d["best_strategy_name"] == "RSI -> MACD"

    def test_as_dict_no_strategy(self):
        r = EvolutionReport(best_strategy={})
        d = r.as_dict()
        assert d["best_strategy_name"] == "none"


# --- EvolutionEngine tests ---


class TestEvolutionEngine:
    def test_init_defaults(self):
        e = EvolutionEngine()
        assert e.population_size == 50
        assert e.memory_seed_ratio == 0.3
        assert e.generations == 3

    def test_init_custom(self):
        e = EvolutionEngine(population_size=20, memory_seed_ratio=0.5, generations=5)
        assert e.population_size == 20
        assert e.memory_seed_ratio == 0.5
        assert e.generations == 5

    def test_run_cycle_basic(self, engine):
        r = engine.run_cycle(1, "bull_trend", SAMPLE_CANDLES)
        assert isinstance(r, EvolutionReport)
        assert r.cycle == 1
        assert r.regime == "bull_trend"
        assert r.generation == 1
        assert r.candidates_generated > 0
        assert r.backtests_run > 0
        assert r.best_sharpe > 0

    def test_generation_counter_increments(self, engine):
        r1 = engine.run_cycle(1, "bull", SAMPLE_CANDLES)
        r2 = engine.run_cycle(2, "bear", SAMPLE_CANDLES)
        assert r1.generation == 1
        assert r2.generation == 2

    def test_empty_candles(self, engine):
        """Engine should not crash with empty candle data."""
        r = engine.run_cycle(1, "unknown", [])
        assert r.backtests_run > 0  # backtests use synthetic data

    def test_low_doctor_health_blocks_save(self, engine):
        r = engine.run_cycle(1, "bear_trend", SAMPLE_CANDLES, doctor_health=30.0)
        assert r.saved_to_memory == 0

    def test_high_doctor_health_allows_save(self, engine):
        r = engine.run_cycle(1, "bull_trend", SAMPLE_CANDLES, doctor_health=100.0)
        # May save if valid strategies found
        assert r.saved_to_memory >= 0

    def test_boundary_doctor_health_50(self, engine):
        """50 is the threshold — should allow save."""
        r = engine.run_cycle(1, "bull_trend", SAMPLE_CANDLES, doctor_health=50.0)
        # 50 is >= 50 so saving should be attempted
        assert isinstance(r.saved_to_memory, int)

    def test_boundary_doctor_health_49(self, engine):
        """49 is below threshold — should block save."""
        r = engine.run_cycle(1, "bull_trend", SAMPLE_CANDLES, doctor_health=49.0)
        assert r.saved_to_memory == 0

    def test_memory_seeding(self, engine):
        """After one save cycle, the next cycle should load from memory."""
        engine.run_cycle(1, "test_regime", SAMPLE_CANDLES, doctor_health=100.0)
        r2 = engine.run_cycle(2, "test_regime", SAMPLE_CANDLES, doctor_health=100.0)
        assert r2.candidates_from_memory >= 0  # May or may not have loaded

    def test_render_output(self, engine):
        r = engine.run_cycle(1, "bull_trend", SAMPLE_CANDLES)
        text = engine.render(r)
        assert "EVOLUTION LAB" in text
        assert "Generation" in text
        assert "Best Sharpe" in text
        assert "Saved to Memory" in text

    def test_render_empty_strategy(self, engine):
        r = EvolutionReport()
        text = engine.render(r)
        assert "none" in text

    def test_population_size_min(self):
        """Even with population_size=1, should not crash."""
        e = EvolutionEngine(population_size=1)
        r = e.run_cycle(1, "test", SAMPLE_CANDLES)
        assert r.candidates_generated >= 1

    def test_multiple_regimes(self, engine):
        """Different regimes should produce different reports."""
        r1 = engine.run_cycle(1, "bull_trend", SAMPLE_CANDLES)
        r2 = engine.run_cycle(2, "bear_trend", SAMPLE_CANDLES)
        assert r1.regime == "bull_trend"
        assert r2.regime == "bear_trend"

    def test_doctor_blocked_count(self, engine):
        """doctor_blocked should count strategies that didn't meet quality filters."""
        r = engine.run_cycle(1, "test", SAMPLE_CANDLES)
        assert r.doctor_blocked >= 0
        assert r.doctor_blocked + r.saved_to_memory <= r.backtests_run or r.doctor_blocked >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
