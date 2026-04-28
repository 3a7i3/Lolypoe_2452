"""
Tests — Option AJ : ParquetExporter OHLCV.
"""
from __future__ import annotations

import time
import pytest

from agents.data.parquet_exporter import ExportMetadata, ParquetExporter, _OHLCV_COLS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_ohlcv(n: int = 10, start_ts: int = 1_700_000_000_000) -> list[list]:
    """Génère n barres OHLCV synthétiques avec timestamps séquentiels (1h)."""
    interval_ms = 3_600_000
    rows = []
    price = 100.0
    for i in range(n):
        ts = start_ts + i * interval_ms
        rows.append([ts, price, price + 1.0, price - 1.0, price + 0.5, float(1000 + i)])
        price += 0.5
    return rows


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def exporter(tmp_path):
    return ParquetExporter(output_dir=str(tmp_path / "cache"), compression="snappy")


@pytest.fixture
def sample_ohlcv():
    return _make_ohlcv(20)


# ── Tests basiques ────────────────────────────────────────────────────────────

def test_save_returns_metadata(exporter, sample_ohlcv):
    meta = exporter.save("BTC/USDT", "1h", sample_ohlcv)
    assert isinstance(meta, ExportMetadata)
    assert meta.n_bars == 20
    assert meta.symbol == "BTC/USDT"
    assert meta.timeframe == "1h"
    assert meta.compression == "snappy"
    assert meta.file_size_bytes > 0


def test_save_creates_file(exporter, sample_ohlcv, tmp_path):
    exporter.save("BTC/USDT", "1h", sample_ohlcv)
    files = list((tmp_path / "cache").glob("*.parquet"))
    assert len(files) == 1


def test_load_returns_dataframe(exporter, sample_ohlcv):
    import pandas as pd
    exporter.save("BTC/USDT", "1h", sample_ohlcv)
    df = exporter.load("BTC/USDT", "1h")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == _OHLCV_COLS
    assert len(df) == 20


def test_load_missing_returns_empty(exporter):
    import pandas as pd
    df = exporter.load("ETH/USDT", "4h")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == _OHLCV_COLS


# ── Tests colonnes et types ───────────────────────────────────────────────────

def test_timestamp_is_utc_datetime(exporter, sample_ohlcv):
    import pandas as pd
    exporter.save("BTC/USDT", "1h", sample_ohlcv)
    df = exporter.load("BTC/USDT", "1h")
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert str(df["timestamp"].dt.tz) == "UTC"


def test_ohlcv_numeric_columns(exporter, sample_ohlcv):
    import pandas as pd
    exporter.save("BTC/USDT", "1h", sample_ohlcv)
    df = exporter.load("BTC/USDT", "1h")
    for col in ["open", "high", "low", "close", "volume"]:
        assert pd.api.types.is_float_dtype(df[col]), f"{col} should be float"


def test_values_match_input(exporter, sample_ohlcv):
    exporter.save("BTC/USDT", "1h", sample_ohlcv)
    df = exporter.load("BTC/USDT", "1h")
    assert abs(float(df["close"].iloc[0]) - sample_ohlcv[0][4]) < 1e-9


# ── Tests append ──────────────────────────────────────────────────────────────

def test_append_adds_new_bars(exporter):
    first_batch = _make_ohlcv(10, start_ts=1_700_000_000_000)
    second_batch = _make_ohlcv(10, start_ts=1_700_000_000_000 + 10 * 3_600_000)
    exporter.save("BTC/USDT", "1h", first_batch)
    exporter.save("BTC/USDT", "1h", second_batch, append=True)
    df = exporter.load("BTC/USDT", "1h")
    assert len(df) == 20


def test_append_deduplicates_overlap(exporter):
    first_batch = _make_ohlcv(10, start_ts=1_700_000_000_000)
    # 5 barres en commun + 5 nouvelles
    second_batch = _make_ohlcv(10, start_ts=1_700_000_000_000 + 5 * 3_600_000)
    exporter.save("BTC/USDT", "1h", first_batch)
    exporter.save("BTC/USDT", "1h", second_batch, append=True)
    df = exporter.load("BTC/USDT", "1h")
    # 10 originaux + 5 nouveaux = 15
    assert len(df) == 15


def test_overwrite_replaces_data(exporter):
    exporter.save("BTC/USDT", "1h", _make_ohlcv(20))
    exporter.save("BTC/USDT", "1h", _make_ohlcv(5), append=False)
    df = exporter.load("BTC/USDT", "1h")
    assert len(df) == 5


# ── Tests filtres temporels ───────────────────────────────────────────────────

def test_load_with_since_filter(exporter):
    ohlcv = _make_ohlcv(20, start_ts=1_700_000_000_000)
    exporter.save("BTC/USDT", "1h", ohlcv)
    # filtre depuis la 10e barre (index 9)
    since_ts = 1_700_000_000_000 + 10 * 3_600_000
    df = exporter.load("BTC/USDT", "1h", since_ts=since_ts)
    assert len(df) == 10


def test_load_with_until_filter(exporter):
    ohlcv = _make_ohlcv(20, start_ts=1_700_000_000_000)
    exporter.save("BTC/USDT", "1h", ohlcv)
    until_ts = 1_700_000_000_000 + 9 * 3_600_000
    df = exporter.load("BTC/USDT", "1h", until_ts=until_ts)
    assert len(df) == 10


def test_load_with_since_and_until(exporter):
    ohlcv = _make_ohlcv(20, start_ts=1_700_000_000_000)
    exporter.save("BTC/USDT", "1h", ohlcv)
    since_ts = 1_700_000_000_000 + 5 * 3_600_000
    until_ts = 1_700_000_000_000 + 14 * 3_600_000
    df = exporter.load("BTC/USDT", "1h", since_ts=since_ts, until_ts=until_ts)
    assert len(df) == 10


# ── Tests suppression ─────────────────────────────────────────────────────────

def test_delete_existing(exporter, sample_ohlcv):
    exporter.save("BTC/USDT", "1h", sample_ohlcv)
    result = exporter.delete("BTC/USDT", "1h")
    assert result is True
    df = exporter.load("BTC/USDT", "1h")
    assert len(df) == 0


def test_delete_nonexistent(exporter):
    result = exporter.delete("ETH/USDT", "4h")
    assert result is False


# ── Tests inventaire ──────────────────────────────────────────────────────────

def test_list_available_empty(exporter):
    assert exporter.list_available() == []


def test_list_available_one_file(exporter, sample_ohlcv):
    exporter.save("BTC/USDT", "1h", sample_ohlcv)
    items = exporter.list_available()
    assert len(items) == 1
    assert items[0]["symbol"] == "BTC/USDT"
    assert items[0]["timeframe"] == "1h"
    assert items[0]["size_bytes"] > 0


def test_list_available_multiple(exporter):
    exporter.save("BTC/USDT", "1h", _make_ohlcv(5))
    exporter.save("ETH/USDT", "4h", _make_ohlcv(5))
    items = exporter.list_available()
    assert len(items) == 2


def test_list_available_filter_symbol(exporter):
    exporter.save("BTC/USDT", "1h", _make_ohlcv(5))
    exporter.save("ETH/USDT", "4h", _make_ohlcv(5))
    items = exporter.list_available(symbol="BTC/USDT")
    assert len(items) == 1
    assert items[0]["symbol"] == "BTC/USDT"


# ── Tests edge cases ──────────────────────────────────────────────────────────

def test_save_empty_ohlcv(exporter):
    meta = exporter.save("BTC/USDT", "1h", [])
    assert meta.n_bars == 0


def test_directory_created_automatically(tmp_path):
    deep_dir = tmp_path / "a" / "b" / "c"
    exp = ParquetExporter(output_dir=str(deep_dir))
    assert deep_dir.exists()


def test_symbol_with_colon(exporter):
    ohlcv = _make_ohlcv(5)
    meta = exporter.save("BTC:USDT", "1h", ohlcv)
    assert meta.n_bars == 5
    df = exporter.load("BTC:USDT", "1h")
    assert len(df) == 5


def test_metadata_exported_at_is_iso(exporter, sample_ohlcv):
    import datetime as dt
    meta = exporter.save("BTC/USDT", "1h", sample_ohlcv)
    # Doit parser sans erreur
    dt.datetime.fromisoformat(meta.exported_at)


def test_parquet_unavailable_raises(monkeypatch):
    import agents.data.parquet_exporter as mod
    monkeypatch.setattr(mod, "_PARQUET_AVAILABLE", False)
    with pytest.raises(ImportError, match="pandas"):
        ParquetExporter(output_dir="/tmp/x")
