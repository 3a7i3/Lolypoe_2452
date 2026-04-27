"""Tests pour les options G (live ticker feed) et I (métriques par exchange).

Exécuter depuis la racine du workspace :
    python -m pytest quant-hedge-ai/test_live_feed_metrics.py -v
"""
from __future__ import annotations

import time
import threading
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import des classes sous test
# ---------------------------------------------------------------------------
from agents.market.market_scanner import (
    _ExchangeMetrics,
    _LiveTickerFeed,
    MarketScanner,
)


# ===========================================================================
# Tests _ExchangeMetrics (option I)
# ===========================================================================


class TestExchangeMetrics:
    def test_initial_state(self):
        m = _ExchangeMetrics(name="binance")
        assert m.calls == 0
        assert m.successes == 0
        assert m.failures == 0
        assert m.avg_latency_ms == 0.0
        assert m.success_rate == 0.0
        assert m.last_success_at == 0.0

    def test_record_success(self):
        m = _ExchangeMetrics(name="binance")
        m.record_success(latency_ms=120.5)
        assert m.calls == 1
        assert m.successes == 1
        assert m.failures == 0
        assert m.avg_latency_ms == pytest.approx(120.5)
        assert m.success_rate == pytest.approx(1.0)
        assert m.last_success_at > 0

    def test_record_failure(self):
        m = _ExchangeMetrics(name="kraken")
        m.record_failure()
        assert m.calls == 1
        assert m.successes == 0
        assert m.failures == 1
        assert m.success_rate == 0.0
        assert m.avg_latency_ms == 0.0

    def test_mixed_calls(self):
        m = _ExchangeMetrics(name="okx")
        m.record_success(100.0)
        m.record_success(200.0)
        m.record_failure()
        assert m.calls == 3
        assert m.successes == 2
        assert m.failures == 1
        assert m.success_rate == pytest.approx(2 / 3)
        assert m.avg_latency_ms == pytest.approx(150.0)

    def test_avg_latency_zero_successes(self):
        m = _ExchangeMetrics(name="test")
        m.record_failure()
        assert m.avg_latency_ms == 0.0


# ===========================================================================
# Tests _LiveTickerFeed (option G)
# ===========================================================================


class TestLiveTickerFeed:
    def _make_exchange(self, tickers: dict | None = None) -> MagicMock:
        exchange = MagicMock()
        exchange.fetch_tickers.return_value = tickers or {
            "BTC/USDT": {"last": 50000.0, "open": 49000.0, "high": 51000.0, "low": 48000.0, "baseVolume": 100.0},
        }
        return exchange

    def test_is_fresh_false_before_start(self):
        feed = _LiveTickerFeed(
            exchanges={"binance": self._make_exchange()},
            symbols=["BTCUSDT"],
            interval=5.0,
        )
        assert feed.is_fresh is False

    def test_snapshot_populated_after_refresh(self):
        feed = _LiveTickerFeed(
            exchanges={"binance": self._make_exchange()},
            symbols=["BTCUSDT"],
            interval=5.0,
        )
        feed._refresh()
        assert feed.latest_snapshot is not None
        assert feed.latest_snapshot["data_source"] == "binance_ws"
        candles = feed.latest_snapshot["candles"]
        assert len(candles) == 1
        assert candles[0]["symbol"] == "BTCUSDT"
        assert candles[0]["close"] == pytest.approx(50000.0)

    def test_is_fresh_after_refresh(self):
        feed = _LiveTickerFeed(
            exchanges={"binance": self._make_exchange()},
            symbols=["BTCUSDT"],
            interval=5.0,
        )
        feed._refresh()
        assert feed.is_fresh is True

    def test_is_fresh_false_when_stale(self):
        feed = _LiveTickerFeed(
            exchanges={"binance": self._make_exchange()},
            symbols=["BTCUSDT"],
            interval=5.0,
        )
        feed._refresh()
        # Simuler un snapshot périmé
        feed.latest_snapshot["fetched_at"] = time.monotonic() - 20  # > 2*5=10s
        assert feed.is_fresh is False

    def test_fallback_to_next_exchange(self):
        bad_exchange = MagicMock()
        bad_exchange.fetch_tickers.side_effect = RuntimeError("API down")
        good_exchange = self._make_exchange()

        feed = _LiveTickerFeed(
            exchanges={"broken": bad_exchange, "binance": good_exchange},
            symbols=["BTCUSDT"],
            interval=5.0,
        )
        feed._refresh()
        # Doit avoir réussi via le 2e exchange
        assert feed.latest_snapshot is not None
        assert feed.latest_snapshot["data_source"] == "binance_ws"

    def test_all_exchanges_fail_no_snapshot(self):
        bad = MagicMock()
        bad.fetch_tickers.side_effect = RuntimeError("down")
        feed = _LiveTickerFeed(
            exchanges={"broken": bad},
            symbols=["BTCUSDT"],
            interval=5.0,
        )
        feed._refresh()
        # Snapshot reste None si tous échouent
        assert feed.latest_snapshot is None

    def test_stop_sets_event(self):
        feed = _LiveTickerFeed(
            exchanges={"binance": self._make_exchange()},
            symbols=["BTCUSDT"],
            interval=0.1,
        )
        # On ne lance pas vraiment le thread pour éviter les effets de bord
        feed.stop()
        assert feed._stop_event.is_set()

    def test_start_stop_thread_lifecycle(self):
        """Test que le thread démarre et s'arrête proprement."""
        feed = _LiveTickerFeed(
            exchanges={"binance": self._make_exchange()},
            symbols=["BTCUSDT"],
            interval=0.1,
        )
        feed.start()
        assert feed._thread.is_alive()
        feed.stop()
        feed._thread.join(timeout=2.0)
        assert not feed._thread.is_alive()


# ===========================================================================
# Tests MarketScanner avec live feed (option G intégration)
# ===========================================================================


class TestMarketScannerLiveFeed:
    def _make_scanner_no_feed(self) -> MarketScanner:
        scanner = MarketScanner(symbols=["BTCUSDT"], live_feed_interval=0.0)
        scanner._exchange = None  # désactive CCXT
        return scanner

    def test_scanner_no_live_feed_by_default(self):
        scanner = self._make_scanner_no_feed()
        assert scanner._live_feed is None

    def test_scanner_stop_noop_without_feed(self):
        scanner = self._make_scanner_no_feed()
        scanner.stop()  # ne doit pas lever d'exception
        assert scanner._live_feed is None

    def test_scanner_stop_with_feed(self):
        """scanner.stop() appelle _live_feed.stop() et met _live_feed à None."""
        mock_feed = MagicMock()
        scanner = self._make_scanner_no_feed()
        scanner._live_feed = mock_feed
        scanner.stop()
        mock_feed.stop.assert_called_once()
        assert scanner._live_feed is None

    def test_scan_uses_live_feed_when_fresh(self):
        """scan() doit utiliser le snapshot du live feed s'il est frais."""
        scanner = self._make_scanner_no_feed()
        fresh_snapshot = {
            "candles": [{"symbol": "BTCUSDT", "close": 60000.0, "open": 59000.0,
                         "high": 61000.0, "low": 58000.0, "volume": 200.0,
                         "timestamp": "2024-01-01T00:00:00+00:00"}],
            "data_source": "binance_ws",
            "fetched_at": time.monotonic(),
        }
        mock_feed = MagicMock()
        mock_feed.is_fresh = True
        mock_feed.latest_snapshot = fresh_snapshot
        scanner._live_feed = mock_feed

        result = scanner.scan()
        assert result["data_source"] == "binance_ws"
        assert len(result["candles"]) == 1
        assert result["candles"][0]["close"] == pytest.approx(60000.0)

    def test_scan_falls_back_when_feed_stale(self):
        """scan() tombe sur synthétique si le live feed n'est pas frais (pas d'exchange)."""
        scanner = self._make_scanner_no_feed()
        mock_feed = MagicMock()
        mock_feed.is_fresh = False
        scanner._live_feed = mock_feed

        result = scanner.scan()
        assert result["data_source"] == "synthetic_fallback"


# ===========================================================================
# Tests get_metrics_report() (option I)
# ===========================================================================


class TestGetMetricsReport:
    def test_empty_metrics(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], exchanges=["binance"])
        scanner._metrics = {}
        report = scanner.get_metrics_report()
        assert "Aucune donnée" in report

    def test_report_format(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], exchanges=["binance"])
        scanner._exchange = None
        m = scanner._metrics["binance"]
        m.record_success(150.0)
        m.record_failure()

        report = scanner.get_metrics_report()
        assert "binance" in report
        assert "appels=" in report and "2" in report
        assert "succès=" in report and "1" in report
        assert "échecs=" in report and "1" in report
        assert "taux=50%" in report

    def test_report_status_icons(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], exchanges=["binance"])
        scanner._exchange = None
        m = scanner._metrics["binance"]
        # success_rate = 1.0 → 🟢
        m.record_success(100.0)
        report = scanner.get_metrics_report()
        assert "🟢" in report

    def test_report_has_header(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], exchanges=["binance"])
        scanner._exchange = None
        report = scanner.get_metrics_report()
        assert "📊 EXCHANGE METRICS" in report

    def test_report_multiple_exchanges(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], exchanges=["binance", "kraken"])
        scanner._exchange = None
        report = scanner.get_metrics_report()
        assert "binance" in report
        assert "kraken" in report
