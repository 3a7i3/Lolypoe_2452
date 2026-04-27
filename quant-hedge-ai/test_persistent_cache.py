"""Tests pour _PersistentCache et l'intégration cache disque dans MarketScanner (option F)."""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.market.market_scanner import (
    MarketScanner,
    _Cache,
    _PersistentCache,
    _SENTINEL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "test_cache.db"


# ---------------------------------------------------------------------------
# Tests _PersistentCache — base
# ---------------------------------------------------------------------------

class TestPersistentCacheInit:
    def test_creates_file(self, tmp_path):
        db = _tmp_db(tmp_path)
        _PersistentCache(ttl_seconds=60, db_path=db)
        assert db.exists()

    def test_creates_parent_dirs(self, tmp_path):
        db = tmp_path / "sub" / "deep" / "cache.db"
        _PersistentCache(ttl_seconds=60, db_path=db)
        assert db.exists()

    def test_creates_table(self, tmp_path):
        db = _tmp_db(tmp_path)
        _PersistentCache(ttl_seconds=60, db_path=db)
        conn = sqlite3.connect(str(db))
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        assert "cache_entries" in tables

    def test_inherits_from_cache(self, tmp_path):
        pc = _PersistentCache(ttl_seconds=60, db_path=_tmp_db(tmp_path))
        assert isinstance(pc, _Cache)


class TestPersistentCacheSetGet:
    def test_set_writes_to_disk(self, tmp_path):
        db = _tmp_db(tmp_path)
        pc = _PersistentCache(ttl_seconds=60, db_path=db)
        pc.set("k1", {"candles": [1, 2, 3], "data_source": "binance_real"})

        conn = sqlite3.connect(str(db))
        row = conn.execute("SELECT value_json FROM cache_entries WHERE key = 'k1'").fetchone()
        conn.close()
        assert row is not None
        assert json.loads(row[0])["data_source"] == "binance_real"

    def test_get_returns_value_from_memory(self, tmp_path):
        pc = _PersistentCache(ttl_seconds=60, db_path=_tmp_db(tmp_path))
        pc.set("k1", {"x": 42})
        result = pc.get("k1")
        assert result is not _SENTINEL
        assert result["x"] == 42

    def test_ttl_zero_disables_disk_write(self, tmp_path):
        db = _tmp_db(tmp_path)
        pc = _PersistentCache(ttl_seconds=0, db_path=db)
        pc.set("k1", {"x": 1})
        conn = sqlite3.connect(str(db))
        count = conn.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0]
        conn.close()
        assert count == 0

    def test_get_after_ttl_expired(self, tmp_path):
        pc = _PersistentCache(ttl_seconds=0.05, db_path=_tmp_db(tmp_path))
        pc.set("k1", {"x": 1})
        time.sleep(0.1)
        assert pc.get("k1") is _SENTINEL


class TestPersistentCacheWarmStart:
    def test_reloads_entries_on_new_instance(self, tmp_path):
        db = _tmp_db(tmp_path)
        pc1 = _PersistentCache(ttl_seconds=60, db_path=db)
        pc1.set("scan:1h", {"candles": [{"close": 99.9}], "data_source": "kraken_real"})

        # Nouvelle instance — simule un redémarrage
        pc2 = _PersistentCache(ttl_seconds=60, db_path=db)
        result = pc2.get("scan:1h")
        assert result is not _SENTINEL
        assert result["data_source"] == "kraken_real"
        assert result["candles"][0]["close"] == 99.9

    def test_does_not_reload_expired_entries(self, tmp_path):
        db = _tmp_db(tmp_path)
        pc1 = _PersistentCache(ttl_seconds=0.05, db_path=db)
        pc1.set("k_expired", {"x": 1})
        time.sleep(0.1)

        pc2 = _PersistentCache(ttl_seconds=60, db_path=db)
        assert pc2.get("k_expired") is _SENTINEL

    def test_multiple_keys_reloaded(self, tmp_path):
        db = _tmp_db(tmp_path)
        pc1 = _PersistentCache(ttl_seconds=60, db_path=db)
        pc1.set("key_a", {"v": "a"})
        pc1.set("key_b", {"v": "b"})
        pc1.set("key_c", {"v": "c"})

        pc2 = _PersistentCache(ttl_seconds=60, db_path=db)
        assert pc2.get("key_a")["v"] == "a"
        assert pc2.get("key_b")["v"] == "b"
        assert pc2.get("key_c")["v"] == "c"


class TestPersistentCacheInvalidate:
    def test_invalidate_key_removes_from_disk(self, tmp_path):
        db = _tmp_db(tmp_path)
        pc = _PersistentCache(ttl_seconds=60, db_path=db)
        pc.set("k1", {"x": 1})
        pc.set("k2", {"x": 2})
        pc.invalidate("k1")

        conn = sqlite3.connect(str(db))
        count = conn.execute("SELECT COUNT(*) FROM cache_entries WHERE key = 'k1'").fetchone()[0]
        conn.close()
        assert count == 0

        # k2 toujours présent
        conn = sqlite3.connect(str(db))
        count = conn.execute("SELECT COUNT(*) FROM cache_entries WHERE key = 'k2'").fetchone()[0]
        conn.close()
        assert count == 1

    def test_invalidate_all_clears_disk(self, tmp_path):
        db = _tmp_db(tmp_path)
        pc = _PersistentCache(ttl_seconds=60, db_path=db)
        pc.set("k1", {"x": 1})
        pc.set("k2", {"x": 2})
        pc.invalidate()

        conn = sqlite3.connect(str(db))
        count = conn.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0]
        conn.close()
        assert count == 0


class TestPersistentCachePurge:
    def test_purge_expired_removes_old_entries(self, tmp_path):
        db = _tmp_db(tmp_path)
        pc = _PersistentCache(ttl_seconds=60, db_path=db)

        # Insérer une entrée déjà expirée directement dans SQLite
        conn = sqlite3.connect(str(db))
        conn.execute(
            "INSERT OR REPLACE INTO cache_entries (key, value_json, expires_at) VALUES (?, ?, ?)",
            ("expired_key", '{"x": 1}', time.time() - 10),
        )
        conn.commit()
        conn.close()

        # Insérer une entrée valide via l'API
        pc.set("valid_key", {"x": 2})

        removed = pc.purge_expired()
        assert removed >= 1

        conn = sqlite3.connect(str(db))
        count = conn.execute("SELECT COUNT(*) FROM cache_entries WHERE key = 'expired_key'").fetchone()[0]
        conn.close()
        assert count == 0


# ---------------------------------------------------------------------------
# Tests MarketScanner — intégration cache persistant
# ---------------------------------------------------------------------------

class TestMarketScannerPersistentCache:
    def test_scanner_with_cache_db_uses_persistent_cache(self, tmp_path):
        db = _tmp_db(tmp_path)
        scanner = MarketScanner(
            symbols=["BTCUSDT"],
            cache_ttl=60,
            exchanges=["binance"],
            cache_db_path=db,
        )
        assert isinstance(scanner._cache, _PersistentCache)

    def test_scanner_without_cache_db_uses_memory_cache(self):
        scanner = MarketScanner(symbols=["BTCUSDT"], cache_ttl=60, exchanges=["binance"])
        assert type(scanner._cache) is _Cache  # exactement _Cache, pas une sous-classe

    def test_scan_result_persisted_to_disk(self, tmp_path):
        db = _tmp_db(tmp_path)
        scanner = MarketScanner(
            symbols=["BTCUSDT"],
            cache_ttl=60,
            exchanges=["binance"],
            cache_db_path=db,
        )
        mock_exchange = MagicMock()
        mock_exchange.fetch_ohlcv.return_value = [
            [1_700_000_000_000, 42000.0, 43000.0, 41000.0, 42500.0, 1500.0]
        ]
        scanner._exchange = mock_exchange
        result = scanner.scan()
        assert result["data_source"] == "binance_real"

        # Vérifier que la donnée est sur disque
        conn = sqlite3.connect(str(db))
        count = conn.execute("SELECT COUNT(*) FROM cache_entries WHERE key LIKE 'scan:%'").fetchone()[0]
        conn.close()
        assert count == 1

    def test_warm_start_serves_scan_from_disk(self, tmp_path):
        db = _tmp_db(tmp_path)

        # Premier scanner — fait un vrai scan
        scanner1 = MarketScanner(
            symbols=["BTCUSDT"],
            cache_ttl=60,
            exchanges=["binance"],
            cache_db_path=db,
        )
        mock_exchange = MagicMock()
        mock_exchange.fetch_ohlcv.return_value = [
            [1_700_000_000_000, 42000.0, 43000.0, 41000.0, 42500.0, 1500.0]
        ]
        scanner1._exchange = mock_exchange
        scanner1.scan()

        # Deuxième scanner — redémarrage, ne devrait pas appeler l'API
        scanner2 = MarketScanner(
            symbols=["BTCUSDT"],
            cache_ttl=60,
            exchanges=["binance"],
            cache_db_path=db,
        )
        # Pas d'exchange configuré → si le cache est manqué, scan() retourne synthétique
        scanner2._exchanges = {}
        result = scanner2.scan()

        # Le cache disque doit avoir été rechargé → données réelles servies
        assert result["data_source"] == "binance_real"
        assert result["candles"][0]["close"] == 42500.0


# ---------------------------------------------------------------------------
# Tests RuntimeConfig — nouveau champ ccxt_cache_db
# ---------------------------------------------------------------------------

class TestRuntimeConfigCacheDb:
    def test_default_cache_db_is_empty(self):
        from runtime_config import RuntimeConfig
        cfg = RuntimeConfig()
        assert cfg.ccxt_cache_db == ""

    def test_env_var_sets_cache_db(self, monkeypatch):
        from runtime_config import load_runtime_config_from_env
        monkeypatch.setenv("V9_CCXT_CACHE_DB", "databases/market_cache.db")
        cfg = load_runtime_config_from_env()
        assert cfg.ccxt_cache_db == "databases/market_cache.db"
