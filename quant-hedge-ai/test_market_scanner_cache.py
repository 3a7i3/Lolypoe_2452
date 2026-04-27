"""Tests unitaires du cache TTL et du MarketScanner avec cache."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.market.market_scanner import _Cache, _SENTINEL, MarketScanner


# ---------------------------------------------------------------------------
# Tests de _Cache
# ---------------------------------------------------------------------------

class TestCache:
    def test_miss_initial(self):
        cache = _Cache(ttl_seconds=10)
        assert cache.get("absent") is _SENTINEL

    def test_set_puis_get(self):
        cache = _Cache(ttl_seconds=10)
        cache.set("k", [1, 2, 3])
        assert cache.get("k") == [1, 2, 3]

    def test_expiration(self):
        cache = _Cache(ttl_seconds=0.05)  # 50 ms
        cache.set("k", "valeur")
        time.sleep(0.1)
        assert cache.get("k") is _SENTINEL

    def test_pas_expire_avant_ttl(self):
        cache = _Cache(ttl_seconds=5)
        cache.set("k", "valeur")
        time.sleep(0.01)
        assert cache.get("k") == "valeur"

    def test_ttl_zero_desactive_cache(self):
        cache = _Cache(ttl_seconds=0)
        cache.set("k", "jamais_servi")
        assert cache.get("k") is _SENTINEL

    def test_invalidate_cle(self):
        cache = _Cache(ttl_seconds=10)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.invalidate("a")
        assert cache.get("a") is _SENTINEL
        assert cache.get("b") == 2

    def test_invalidate_tout(self):
        cache = _Cache(ttl_seconds=10)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.invalidate()
        assert cache.get("a") is _SENTINEL
        assert cache.get("b") is _SENTINEL

    def test_size(self):
        cache = _Cache(ttl_seconds=10)
        assert cache.size == 0
        cache.set("x", 42)
        assert cache.size == 1
        cache.set("y", 43)
        assert cache.size == 2

    def test_valeur_none_stockable(self):
        """None est une valeur valide distincte du sentinel."""
        cache = _Cache(ttl_seconds=10)
        cache.set("k", None)
        result = cache.get("k")
        assert result is not _SENTINEL
        assert result is None


# ---------------------------------------------------------------------------
# Helpers pour les tests scanner
# ---------------------------------------------------------------------------

_FAKE_OHLCV = [[1_714_003_600_000, 77_000.0, 77_500.0, 76_900.0, 77_200.0, 420.0]]
_FAKE_HISTORY = [[1_714_000_000_000 + i * 3_600_000, 77_000.0, 77_500.0, 76_900.0, 77_000.0 + i * 10, 420.0]
                 for i in range(200)]


def _mock_exchange(ohlcv=_FAKE_OHLCV, history=_FAKE_HISTORY):
    exchange = MagicMock()

    def fetch(ccxt_symbol, timeframe, limit=2):
        if limit <= 2:
            return ohlcv
        return history[:limit]

    exchange.fetch_ohlcv.side_effect = fetch
    return exchange


# ---------------------------------------------------------------------------
# Tests cache dans scan()
# ---------------------------------------------------------------------------

class TestScanCache:
    def test_scan_appelle_binance_une_seule_fois(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=60)
        scanner._exchange = _mock_exchange()

        scanner.scan()
        scanner.scan()
        scanner.scan()

        # Un seul appel réseau malgré 3 scan()
        assert scanner._exchange.fetch_ohlcv.call_count == 1

    def test_scan_rappelle_apres_expiration(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=0.05)
        scanner._exchange = _mock_exchange()

        scanner.scan()
        time.sleep(0.1)  # attendre expiration
        scanner.scan()

        assert scanner._exchange.fetch_ohlcv.call_count == 2

    def test_scan_cache_desactive_appelle_toujours_reseau(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=0)
        scanner._exchange = _mock_exchange()

        scanner.scan()
        scanner.scan()
        scanner.scan()

        assert scanner._exchange.fetch_ohlcv.call_count == 3

    def test_scan_cache_retourne_meme_donnees(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=60)
        scanner._exchange = _mock_exchange()

        r1 = scanner.scan()
        r2 = scanner.scan()

        assert r1["candles"][0]["close"] == r2["candles"][0]["close"]

    def test_scan_synthetique_non_mis_en_cache(self):
        """Si Binance échoue, le fallback synthétique ne pollue pas le cache."""
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=60)
        exchange = MagicMock()
        exchange.fetch_ohlcv.side_effect = Exception("timeout")
        scanner._exchange = exchange

        scanner.scan()
        scanner.scan()

        # Deux appels (chaque fois on essaie Binance)
        assert exchange.fetch_ohlcv.call_count == 2
        # Cache vide
        assert scanner._cache.size == 0


# ---------------------------------------------------------------------------
# Tests cache dans fetch_history()
# ---------------------------------------------------------------------------

class TestFetchHistoryCache:
    def test_history_appelle_binance_une_seule_fois(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=60)
        scanner._exchange = _mock_exchange()

        scanner.fetch_history("BTCUSDT", limit=200)
        scanner.fetch_history("BTCUSDT", limit=200)

        assert scanner._exchange.fetch_ohlcv.call_count == 1

    def test_history_rappelle_apres_expiration(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=0.05)
        scanner._exchange = _mock_exchange()

        scanner.fetch_history("BTCUSDT", limit=200)
        time.sleep(0.1)
        scanner.fetch_history("BTCUSDT", limit=200)

        assert scanner._exchange.fetch_ohlcv.call_count == 2

    def test_cles_cache_distinctes_par_symbole(self):
        scanner = MarketScanner(symbols=["BTCUSDT", "ETHUSDT"], cache_ttl=60)
        scanner._exchange = _mock_exchange()

        scanner.fetch_history("BTCUSDT", limit=200)
        scanner.fetch_history("ETHUSDT", limit=200)
        scanner.fetch_history("BTCUSDT", limit=200)  # depuis le cache
        scanner.fetch_history("ETHUSDT", limit=200)  # depuis le cache

        # 2 appels réseau (un par symbole)
        assert scanner._exchange.fetch_ohlcv.call_count == 2

    def test_cles_cache_distinctes_par_limit(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=60)
        scanner._exchange = _mock_exchange()

        scanner.fetch_history("BTCUSDT", limit=100)
        scanner.fetch_history("BTCUSDT", limit=200)

        # limit différente → clé différente → 2 appels
        assert scanner._exchange.fetch_ohlcv.call_count == 2


# ---------------------------------------------------------------------------
# Tests isolation scan vs history
# ---------------------------------------------------------------------------

class TestScanVsHistoryCache:
    def test_scan_et_history_partagent_pas_le_cache(self):
        """scan() et fetch_history() ont des clés de cache distinctes."""
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=60)
        scanner._exchange = _mock_exchange()

        scanner.scan()            # 1 appel
        scanner.fetch_history("BTCUSDT", limit=200)  # 1 appel (clé différente)

        assert scanner._exchange.fetch_ohlcv.call_count == 2


# ---------------------------------------------------------------------------
# Test config env → cache_ttl
# ---------------------------------------------------------------------------

def test_runtime_config_cache_ttl():
    import os
    from runtime_config import load_runtime_config_from_env

    os.environ["V9_CCXT_CACHE_TTL"] = "120"
    try:
        cfg = load_runtime_config_from_env()
        assert cfg.ccxt_cache_ttl == 120.0
    finally:
        os.environ.pop("V9_CCXT_CACHE_TTL", None)


def test_runtime_config_cache_ttl_defaut():
    import os
    from runtime_config import load_runtime_config_from_env

    os.environ.pop("V9_CCXT_CACHE_TTL", None)
    cfg = load_runtime_config_from_env()
    assert cfg.ccxt_cache_ttl == 60.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
