"""Tests de l'indicateur de source de données dans le dashboard."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.market.market_scanner import MarketScanner
from dashboard.control_center import AIControlCenter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_OHLCV = [[1_714_003_600_000, 77_000.0, 77_500.0, 76_900.0, 77_200.0, 420.0]]


def _mock_exchange(fail: bool = False):
    exchange = MagicMock()
    if fail:
        exchange.fetch_ohlcv.side_effect = Exception("timeout")
    else:
        exchange.fetch_ohlcv.return_value = _FAKE_OHLCV
    return exchange


def _minimal_report(cc: AIControlCenter, data_source_info: dict) -> str:
    return cc.render_full_report(
        cycle=1,
        market_regime={"regime": "neutral", "strategy_type": "balanced",
                       "momentum": 0.0, "realized_volatility": 0.02, "anomalies": []},
        whale_data={"alerts": [], "threat_level": "low"},
        best_strategy=None,
        stats={"total_strategies": 0, "avg_sharpe": 0.0, "best_sharpe": 0.0, "median_sharpe": 0.0},
        allocation={},
        brain_info={"kelly_fraction": 0.25, "vol_target": 0.02, "max_position": 0.3},
        decision={"should_trade": False, "reason": "test", "risk_limits": {}},
        health={"status": "running", "agents_count": 1, "strategies_gen": 0,
                "backtests_completed": 0, "model_version": 1},
        data_source_info=data_source_info,
    )


# ---------------------------------------------------------------------------
# Tests scan() — champ data_source
# ---------------------------------------------------------------------------

class TestScanDataSource:
    def test_scan_binance_real(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=0)
        scanner._exchange = _mock_exchange(fail=False)
        result = scanner.scan()
        assert result["data_source"] == "binance_real"

    def test_scan_synthetic_fallback_si_exchange_none(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=0)
        scanner._exchange = None
        result = scanner.scan()
        assert result["data_source"] == "synthetic_fallback"

    def test_scan_synthetic_fallback_si_api_plante(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=0)
        scanner._exchange = _mock_exchange(fail=True)
        result = scanner.scan()
        assert result["data_source"] == "synthetic_fallback"

    def test_scan_depuis_cache_reste_binance_real(self):
        """Les données servies depuis le cache gardent la source 'binance_real'."""
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=60)
        scanner._exchange = _mock_exchange(fail=False)
        scanner.scan()  # remplit le cache
        scanner._exchange = None  # coupe l'accès Binance
        result = scanner.scan()  # doit venir du cache
        assert result["data_source"] == "binance_real"

    def test_scan_candles_toujours_present(self):
        """Quelle que soit la source, 'candles' doit être présent."""
        for fail in (True, False):
            scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=0)
            scanner._exchange = _mock_exchange(fail=fail)
            result = scanner.scan()
            assert "candles" in result
            assert "data_source" in result


# ---------------------------------------------------------------------------
# Tests render_data_source()
# ---------------------------------------------------------------------------

class TestRenderDataSource:
    def setup_method(self):
        self.cc = AIControlCenter()

    def test_binance_real_affiche_vert(self):
        out = self.cc.render_data_source("binance_real", candle_count=4, history_count=200, timeframe="1h")
        assert "🟢" in out
        assert "BINANCE LIVE" in out
        assert "4" in out
        assert "200" in out
        assert "1h" in out

    def test_synthetic_affiche_jaune(self):
        out = self.cc.render_data_source("synthetic_fallback", candle_count=4, history_count=0, timeframe="1h")
        assert "🟡" in out
        assert "SYNTHÉTIQUE" in out

    def test_timeframe_affiché(self):
        out = self.cc.render_data_source("binance_real", candle_count=4, history_count=200, timeframe="4h")
        assert "4h" in out


# ---------------------------------------------------------------------------
# Tests render_header() avec badge source
# ---------------------------------------------------------------------------

class TestRenderHeader:
    def setup_method(self):
        self.cc = AIControlCenter()

    def test_header_binance_real(self):
        out = self.cc.render_header(1, "2026-01-01T00:00:00+00:00", data_source="binance_real")
        assert "🟢" in out
        assert "BINANCE LIVE" in out

    def test_header_synthetic(self):
        out = self.cc.render_header(1, "2026-01-01T00:00:00+00:00", data_source="synthetic_fallback")
        assert "🟡" in out
        assert "SYNTHÉTIQUE" in out

    def test_header_source_inconnue(self):
        out = self.cc.render_header(1, "2026-01-01T00:00:00+00:00")
        assert "⚪" in out

    def test_header_contient_cycle(self):
        out = self.cc.render_header(42, "2026-01-01T00:00:00+00:00", data_source="binance_real")
        assert "42" in out


# ---------------------------------------------------------------------------
# Tests render_full_report() intégration
# ---------------------------------------------------------------------------

class TestRenderFullReport:
    def setup_method(self):
        self.cc = AIControlCenter()

    def test_rapport_contient_section_source_si_fournie(self):
        info = {"data_source": "binance_real", "candle_count": 4, "history_count": 200, "timeframe": "1h"}
        out = _minimal_report(self.cc, info)
        assert "SOURCE DONNÉES MARCHÉ" in out
        assert "🟢" in out
        assert "200" in out

    def test_rapport_contient_badge_dans_entete(self):
        info = {"data_source": "binance_real", "candle_count": 4, "history_count": 200, "timeframe": "1h"}
        out = _minimal_report(self.cc, info)
        lines = out.splitlines()
        header_line = next(l for l in lines if "CONTROL CENTER" in l)
        assert "🟢" in header_line

    def test_rapport_synthetique_badge_jaune(self):
        info = {"data_source": "synthetic_fallback", "candle_count": 4, "history_count": 0, "timeframe": "1h"}
        out = _minimal_report(self.cc, info)
        assert "🟡" in out
        assert "SYNTHÉTIQUE" in out

    def test_rapport_sans_data_source_info_reste_valide(self):
        """data_source_info=None ne doit pas faire planter le rapport."""
        out = self.cc.render_full_report(
            cycle=1,
            market_regime={"regime": "neutral", "strategy_type": "balanced",
                           "momentum": 0.0, "realized_volatility": 0.0, "anomalies": []},
            whale_data={"alerts": [], "threat_level": "low"},
            best_strategy=None,
            stats={"total_strategies": 0, "avg_sharpe": 0.0, "best_sharpe": 0.0, "median_sharpe": 0.0},
            allocation={},
            brain_info={"kelly_fraction": 0.25, "vol_target": 0.02, "max_position": 0.3},
            decision={"should_trade": False, "reason": "test", "risk_limits": {}},
            health={"status": "running", "agents_count": 1, "strategies_gen": 0,
                    "backtests_completed": 0, "model_version": 1},
        )
        assert "CONTROL CENTER" in out
        assert "SOURCE DONNÉES MARCHÉ" not in out  # section absente si pas fourni


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
