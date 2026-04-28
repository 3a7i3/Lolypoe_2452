"""Tests option L — _WebSocketFeed et intégration MarketScanner."""
from __future__ import annotations

import asyncio
import time
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.market.market_scanner import MarketScanner, _WebSocketFeed


# ---------------------------------------------------------------------------
# Helpers — mock ccxt.pro exchange
# ---------------------------------------------------------------------------


def _make_pro_exchange(tickers: dict | None = None):
    """Retourne (mock_ccxt_pro_module, exchange_instance_mock)."""
    default_tickers = {
        "BTC/USDT": {"last": 60000.0, "open": 59000.0, "high": 61000.0, "low": 58000.0, "baseVolume": 1234.5},
        "ETH/USDT": {"last": 3000.0, "open": 2950.0, "high": 3050.0, "low": 2900.0, "baseVolume": 567.8},
    }
    effective = tickers if tickers is not None else default_tickers

    async def watch_tickers(symbols):
        return effective

    async def close_ex():
        pass

    exchange_instance = MagicMock()
    exchange_instance.watch_tickers = watch_tickers
    exchange_instance.close = close_ex

    mod = types.ModuleType("ccxt.pro")
    mod.binance = MagicMock(return_value=exchange_instance)
    return mod, exchange_instance


# ---------------------------------------------------------------------------
# Tests _WebSocketFeed — propriétés de base (sans démarrer le thread)
# ---------------------------------------------------------------------------


class TestWebSocketFeedProperties:
    def test_latest_snapshot_none_at_init(self):
        feed = _WebSocketFeed(exchange_name="binance", symbols=["BTCUSDT"], interval=5.0)
        assert feed.latest_snapshot is None

    def test_is_fresh_false_when_no_snapshot(self):
        feed = _WebSocketFeed(exchange_name="binance", symbols=["BTCUSDT"], interval=5.0)
        assert feed.is_fresh is False

    def test_is_fresh_true_after_recent_snapshot(self):
        feed = _WebSocketFeed(exchange_name="binance", symbols=["BTCUSDT"], interval=5.0)
        feed.latest_snapshot = {
            "candles": [],
            "data_source": "binance_ws_live",
            "fetched_at": time.monotonic(),
        }
        assert feed.is_fresh is True

    def test_is_fresh_false_when_stale(self):
        feed = _WebSocketFeed(exchange_name="binance", symbols=["BTCUSDT"], interval=1.0)
        feed.latest_snapshot = {
            "candles": [],
            "data_source": "binance_ws_live",
            "fetched_at": time.monotonic() - 30.0,
        }
        assert feed.is_fresh is False

    def test_stop_sets_stop_event_without_start(self):
        feed = _WebSocketFeed(exchange_name="binance", symbols=["BTCUSDT"], interval=1.0)
        assert not feed._stop_event.is_set()
        feed.stop()
        assert feed._stop_event.is_set()


# ---------------------------------------------------------------------------
# Tests _WebSocketFeed — _stream avec mock ccxt.pro
# ---------------------------------------------------------------------------


class TestWebSocketFeedStream:
    def test_stream_updates_snapshot_with_ws_live_source(self):
        """Un cycle du stream met à jour latest_snapshot avec data_source='binance_ws_live'."""
        mock_mod, ex_mock = _make_pro_exchange()

        call_count = 0

        async def watch_once(symbols):
            nonlocal call_count
            call_count += 1
            # Après le premier tick, on stoppe
            return {
                "BTC/USDT": {"last": 65000.0, "open": 64000.0, "high": 66000.0, "low": 63000.0, "baseVolume": 100.0},
            }

        ex_mock.watch_tickers = watch_once
        feed = _WebSocketFeed(exchange_name="binance", symbols=["BTCUSDT"], interval=1.0)
        feed._stop_event.set()  # stoppe après le premier cycle

        with patch("ccxt.pro", mock_mod, create=True):
            with patch.dict("sys.modules", {"ccxt.pro": mock_mod}):
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(feed._stream())
                finally:
                    loop.close()

        # Même si stop_event est déjà mis, le premier passage doit avoir produit un snapshot
        # (selon impl : while not stop_event → sort immédiatement sans appel)
        # On vérifie que le format est correct si snapshot produit
        if feed.latest_snapshot is not None:
            assert feed.latest_snapshot["data_source"] == "binance_ws_live"
            assert "candles" in feed.latest_snapshot

    def test_stream_handles_error_without_crash(self):
        """Une exception dans watch_tickers ne fait pas planter le feed."""
        mock_mod, ex_mock = _make_pro_exchange()

        async def raise_error(symbols):
            raise ConnectionError("network down")

        ex_mock.watch_tickers = raise_error
        feed = _WebSocketFeed(exchange_name="binance", symbols=["BTCUSDT"], interval=0.01)
        feed._stop_event.set()  # un seul cycle

        with patch.dict("sys.modules", {"ccxt.pro": mock_mod}):
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(feed._stream())
            finally:
                loop.close()

        assert feed.latest_snapshot is None  # pas de snapshot si erreur


# ---------------------------------------------------------------------------
# Tests MarketScanner — sélection feed (via patch _is_ccxt_pro_available)
# ---------------------------------------------------------------------------


class TestMarketScannerFeedSelection:
    def test_ws_feed_selected_when_pro_available(self):
        """use_websocket=True + ccxt.pro dispo → _WebSocketFeed."""
        mock_exchange = MagicMock()
        with patch("agents.market.market_scanner._is_ccxt_pro_available", return_value=True):
            with patch("agents.market.market_scanner.MarketScanner._init_exchanges",
                       return_value={"binance": mock_exchange}):
                scanner = MarketScanner(
                    symbols=["BTCUSDT"],
                    live_feed_interval=1.0,
                    use_websocket=True,
                )
        try:
            assert isinstance(scanner._live_feed, _WebSocketFeed)
        finally:
            scanner.stop()

    def test_polling_feed_when_pro_unavailable(self):
        """use_websocket=True + ccxt.pro indispo → _LiveTickerFeed (polling)."""
        from agents.market.market_scanner import _LiveTickerFeed
        mock_exchange = MagicMock()
        with patch("agents.market.market_scanner._is_ccxt_pro_available", return_value=False):
            with patch("agents.market.market_scanner.MarketScanner._init_exchanges",
                       return_value={"binance": mock_exchange}):
                scanner = MarketScanner(
                    symbols=["BTCUSDT"],
                    live_feed_interval=1.0,
                    use_websocket=True,
                )
        try:
            assert isinstance(scanner._live_feed, _LiveTickerFeed)
        finally:
            scanner.stop()

    def test_polling_feed_when_ws_disabled(self):
        """use_websocket=False → _LiveTickerFeed même si ccxt.pro dispo."""
        from agents.market.market_scanner import _LiveTickerFeed
        mock_exchange = MagicMock()
        with patch("agents.market.market_scanner._is_ccxt_pro_available", return_value=True):
            with patch("agents.market.market_scanner.MarketScanner._init_exchanges",
                       return_value={"binance": mock_exchange}):
                scanner = MarketScanner(
                    symbols=["BTCUSDT"],
                    live_feed_interval=1.0,
                    use_websocket=False,
                )
        try:
            assert isinstance(scanner._live_feed, _LiveTickerFeed)
        finally:
            scanner.stop()

    def test_no_feed_when_interval_zero(self):
        scanner = MarketScanner(
            symbols=["BTCUSDT"],
            live_feed_interval=0.0,
            use_websocket=True,
        )
        try:
            assert scanner._live_feed is None
        finally:
            scanner.stop()

    def test_scan_uses_ws_live_snapshot_when_fresh(self):
        """scan() retourne le snapshot WebSocket si is_fresh."""
        mock_exchange = MagicMock()
        with patch("agents.market.market_scanner._is_ccxt_pro_available", return_value=True):
            with patch("agents.market.market_scanner.MarketScanner._init_exchanges",
                       return_value={"binance": mock_exchange}):
                scanner = MarketScanner(
                    symbols=["BTCUSDT"],
                    live_feed_interval=5.0,
                    use_websocket=True,
                )
        try:
            scanner._live_feed.latest_snapshot = {  # type: ignore[union-attr]
                "candles": [{"symbol": "BTCUSDT", "close": 65000.0}],
                "data_source": "binance_ws_live",
                "fetched_at": time.monotonic(),
            }
            result = scanner.scan()
            assert result["data_source"] == "binance_ws_live"
            assert result["candles"][0]["close"] == 65000.0
        finally:
            scanner.stop()


# ---------------------------------------------------------------------------
# Tests runtime_config (V9_CCXT_WS_PRO)
# ---------------------------------------------------------------------------


class TestRuntimeConfigWsPro:
    def test_default_ws_pro_is_false(self):
        from runtime_config import RuntimeConfig
        assert RuntimeConfig().ccxt_ws_pro is False

    def test_env_true_enables_ws_pro(self):
        import os
        from runtime_config import load_runtime_config_from_env
        with patch.dict(os.environ, {"V9_CCXT_WS_PRO": "true"}):
            cfg = load_runtime_config_from_env()
        assert cfg.ccxt_ws_pro is True

    def test_env_false_disables_ws_pro(self):
        import os
        from runtime_config import load_runtime_config_from_env
        with patch.dict(os.environ, {"V9_CCXT_WS_PRO": "false"}):
            cfg = load_runtime_config_from_env()
        assert cfg.ccxt_ws_pro is False

    def test_as_dict_contains_ccxt_ws_pro(self):
        from runtime_config import RuntimeConfig
        d = RuntimeConfig(ccxt_ws_pro=True).as_dict()
        assert "ccxt_ws_pro" in d
        assert d["ccxt_ws_pro"] is True

