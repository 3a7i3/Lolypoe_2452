"""Tests unitaires du fallback multi-exchange dans MarketScanner."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.market.market_scanner import MarketScanner
from runtime_config import load_runtime_config_from_env

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_OHLCV = [[1_714_003_600_000, 77_000.0, 77_500.0, 76_900.0, 77_200.0, 420.0]]


def _mock_ok():
    """Exchange qui répond correctement."""
    m = MagicMock()
    m.fetch_ohlcv.return_value = _FAKE_OHLCV
    return m


def _mock_fail(exc_msg="timeout"):
    """Exchange qui lève une exception."""
    m = MagicMock()
    m.fetch_ohlcv.side_effect = Exception(exc_msg)
    return m


def _scanner_with(exchanges_dict: dict, **kwargs) -> MarketScanner:
    """Crée un MarketScanner avec exchanges injectés manuellement."""
    names = list(exchanges_dict.keys())
    s = MarketScanner(symbols=["BTCUSDT"], exchanges=names, cache_ttl=0, **kwargs)
    s._exchanges = exchanges_dict
    return s


# ---------------------------------------------------------------------------
# Test : exchange primaire (Binance) disponible
# ---------------------------------------------------------------------------

class TestPrimaryExchange:
    def test_binance_ok_source_binance_real(self):
        s = _scanner_with({"binance": _mock_ok()})
        r = s.scan()
        assert r["data_source"] == "binance_real"

    def test_binance_ok_appelle_binance_pas_les_autres(self):
        binance = _mock_ok()
        kraken = _mock_ok()
        s = _scanner_with({"binance": binance, "kraken": kraken})
        s.scan()
        assert binance.fetch_ohlcv.call_count == 1
        assert kraken.fetch_ohlcv.call_count == 0

    def test_binance_ok_candles_correctes(self):
        s = _scanner_with({"binance": _mock_ok()})
        r = s.scan()
        assert r["candles"][0]["close"] == 77_200.0
        assert r["candles"][0]["symbol"] == "BTCUSDT"


# ---------------------------------------------------------------------------
# Test : Binance down, fallback Kraken
# ---------------------------------------------------------------------------

class TestKrakenFallback:
    def test_binance_down_source_kraken_real(self):
        s = _scanner_with({"binance": _mock_fail(), "kraken": _mock_ok()})
        r = s.scan()
        assert r["data_source"] == "kraken_real"

    def test_binance_down_kraken_appele(self):
        binance = _mock_fail()
        kraken = _mock_ok()
        s = _scanner_with({"binance": binance, "kraken": kraken})
        s.scan()
        assert binance.fetch_ohlcv.call_count == 1
        assert kraken.fetch_ohlcv.call_count == 1

    def test_binance_down_candles_depuis_kraken(self):
        s = _scanner_with({"binance": _mock_fail(), "kraken": _mock_ok()})
        r = s.scan()
        assert r["candles"][0]["close"] == 77_200.0


# ---------------------------------------------------------------------------
# Test : Binance + Kraken down, fallback OKX
# ---------------------------------------------------------------------------

class TestOKXFallback:
    def test_binance_kraken_down_source_okx_real(self):
        s = _scanner_with({"binance": _mock_fail(), "kraken": _mock_fail(), "okx": _mock_ok()})
        r = s.scan()
        assert r["data_source"] == "okx_real"

    def test_trois_exchanges_tentes_dans_ordre(self):
        binance = _mock_fail()
        kraken = _mock_fail()
        okx = _mock_ok()
        s = _scanner_with({"binance": binance, "kraken": kraken, "okx": okx})
        s.scan()
        assert binance.fetch_ohlcv.call_count == 1
        assert kraken.fetch_ohlcv.call_count == 1
        assert okx.fetch_ohlcv.call_count == 1


# ---------------------------------------------------------------------------
# Test : tous les exchanges down → synthetic_fallback
# ---------------------------------------------------------------------------

class TestAllExchangesDown:
    def test_tous_down_source_synthetic_fallback(self):
        s = _scanner_with({"binance": _mock_fail(), "kraken": _mock_fail(), "okx": _mock_fail()})
        r = s.scan()
        assert r["data_source"] == "synthetic_fallback"

    def test_tous_down_candles_generees(self):
        s = _scanner_with({"binance": _mock_fail(), "kraken": _mock_fail(), "okx": _mock_fail()})
        r = s.scan()
        c = r["candles"][0]
        assert "close" in c and "open" in c and "symbol" in c

    def test_aucun_exchange_configure(self):
        s = MarketScanner(symbols=["BTCUSDT"], exchanges=[], cache_ttl=0)
        s._exchanges = {}
        r = s.scan()
        assert r["data_source"] == "synthetic_fallback"


# ---------------------------------------------------------------------------
# Test : fetch_history avec multi-exchange
# ---------------------------------------------------------------------------

_FAKE_HISTORY = [[1_714_000_000_000 + i * 3_600_000, 77_000.0, 77_500.0, 76_900.0, 77_000.0 + i * 10, 420.0]
                 for i in range(50)]


def _mock_history_ok():
    m = MagicMock()
    m.fetch_ohlcv.return_value = _FAKE_HISTORY
    return m


class TestFetchHistoryMultiExchange:
    def test_binance_ok_retourne_historique(self):
        s = _scanner_with({"binance": _mock_history_ok()})
        h = s.fetch_history("BTCUSDT", limit=50)
        assert len(h) == 50
        assert h[0]["symbol"] == "BTCUSDT"

    def test_binance_down_utilise_kraken_pour_historique(self):
        binance = _mock_fail()
        kraken = _mock_history_ok()
        s = _scanner_with({"binance": binance, "kraken": kraken})
        h = s.fetch_history("BTCUSDT", limit=50)
        assert len(h) == 50
        assert binance.fetch_ohlcv.call_count == 1
        assert kraken.fetch_ohlcv.call_count == 1

    def test_tous_down_retourne_liste_vide(self):
        s = _scanner_with({"binance": _mock_fail(), "kraken": _mock_fail()})
        h = s.fetch_history("BTCUSDT", limit=50)
        assert h == []


# ---------------------------------------------------------------------------
# Test : compatibilité rétroactive _exchange (setter/getter)
# ---------------------------------------------------------------------------

class TestExchangeBackwardCompat:
    def test_setter_injecte_dans_exchanges(self):
        s = MarketScanner(symbols=["BTCUSDT"], exchanges=["binance"], cache_ttl=0)
        mock = _mock_ok()
        s._exchange = mock
        assert "binance" in s._exchanges
        assert s._exchanges["binance"] is mock

    def test_getter_retourne_premier_exchange(self):
        s = MarketScanner(symbols=["BTCUSDT"], exchanges=["binance", "kraken"], cache_ttl=0)
        mock_b = _mock_ok()
        mock_k = _mock_ok()
        s._exchanges = {"binance": mock_b, "kraken": mock_k}
        assert s._exchange is mock_b

    def test_setter_none_vide_exchanges(self):
        s = MarketScanner(symbols=["BTCUSDT"], exchanges=["binance"], cache_ttl=0)
        s._exchange = None
        assert s._exchanges == {}
        assert s._exchange is None


# ---------------------------------------------------------------------------
# Test : variable d'environnement V9_CCXT_EXCHANGES
# ---------------------------------------------------------------------------

class TestEnvVarExchanges:
    def test_valeur_par_defaut(self, monkeypatch):
        monkeypatch.delenv("V9_CCXT_EXCHANGES", raising=False)
        cfg = load_runtime_config_from_env()
        assert cfg.ccxt_exchanges == "binance,kraken,okx"

    def test_valeur_personnalisee(self, monkeypatch):
        monkeypatch.setenv("V9_CCXT_EXCHANGES", "kraken,okx")
        cfg = load_runtime_config_from_env()
        assert cfg.ccxt_exchanges == "kraken,okx"

    def test_exchange_unique(self, monkeypatch):
        monkeypatch.setenv("V9_CCXT_EXCHANGES", "binance")
        cfg = load_runtime_config_from_env()
        assert cfg.ccxt_exchanges == "binance"
