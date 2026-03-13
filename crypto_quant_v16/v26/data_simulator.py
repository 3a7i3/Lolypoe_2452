from __future__ import annotations

from datetime import datetime, timedelta
import logging
import random
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd
from cachetools import TTLCache
from v26.dex_adapter import is_dex_exchange, fetch_dex_ohlcv, fetch_dex_orderbook

# V27.3 – WS feed (Binance real-time kline stream, optional)
_get_ws_ohlcv = None
try:
    from v26.ws_feed import get_ws_ohlcv as _get_ws_ohlcv
    _WS_AVAILABLE = True
except Exception:  # pragma: no cover
    _WS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ── TTL caches ────────────────────────────────────────────────────────────────
# OHLCV: 60-second TTL (1-min cache is plenty for hourly/daily charts)
# Orderbook: 10-second TTL (needs to be more real-time)
_ohlcv_cache: TTLCache = TTLCache(maxsize=32, ttl=60)
_book_cache: TTLCache = TTLCache(maxsize=16, ttl=10)

# tracks last successful fetch mode per (symbol, timeframe) → "live" | "mock"
_source_status: Dict[Tuple[str, str, str], str] = {}
_source_meta: Dict[Tuple[str, str, str], Dict[str, object]] = {}
_book_meta: Dict[Tuple[str, str], Dict[str, object]] = {}


def _ccxt_exchange(exchange_name: str = "binance"):
    """Lazy-load a public ccxt exchange instance (no API key for market data)."""
    import ccxt  # noqa: PLC0415
    exchange_cls = getattr(ccxt, str(exchange_name).lower(), None)
    if exchange_cls is None:
        exchange_cls = ccxt.binance
    # Keep market-data calls responsive on unstable networks.
    return exchange_cls({"enableRateLimit": True, "timeout": 10000})


# ── Real market data ───────────────────────────────────────────────────────────

def fetch_ohlcv(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    limit: int = 220,
    exchange_name: str = "binance",
    data_mode: str = "auto",
) -> pd.DataFrame:
    """Fetch OHLCV candles.

    Priority order (Binance only):
      1. WebSocket buffer (V27.3 real-time, zero latency) — when ≥10 closed candles buffered
      2. TTL REST cache (60 s)
      3. Live ccxt REST fetch
      4. Mock fallback
    Non-Binance exchanges use steps 2-4 only.
    """
    mode = str(data_mode).strip().lower()

    if mode == "mock":
        df = _mock_ohlcv(limit)
        _source_status[(symbol, timeframe, exchange_name)] = "mock_forced"
        _source_meta[(symbol, timeframe, exchange_name)] = {
            "last_fetch_utc": datetime.utcnow().isoformat(),
            "latency_ms": -1.0,
            "last_error": "",
            "rows": int(len(df)),
        }
        return df

    # ── V27.3: WS buffer (Binance real-time) ──────────────────────────────────
    if _WS_AVAILABLE and _get_ws_ohlcv is not None and str(exchange_name).lower() == "binance":
        try:
            ws_df = _get_ws_ohlcv(symbol, timeframe, limit)
            if ws_df is not None and not ws_df.empty:
                _source_status[(symbol, timeframe, exchange_name)] = "ws_live"
                _source_meta[(symbol, timeframe, exchange_name)] = {
                    "last_fetch_utc": datetime.utcnow().isoformat(),
                    "latency_ms": 0.0,
                    "last_error": "",
                    "rows": int(len(ws_df)),
                }
                return ws_df
        except Exception as ws_exc:
            logger.debug("WS buffer skipped (%s), falling back to REST", ws_exc)

    # ── DEX adapter path (Uniswap/Hyperliquid + pluggable providers) ─────────
    if is_dex_exchange(exchange_name):
        df, src, err = fetch_dex_ohlcv(symbol, timeframe, limit, exchange_name, data_mode=mode)
        if df is not None and not df.empty:
            cache_key = (symbol, timeframe, limit, exchange_name)
            _ohlcv_cache[cache_key] = df
            _source_status[(symbol, timeframe, exchange_name)] = src
            _source_meta[(symbol, timeframe, exchange_name)] = {
                "last_fetch_utc": datetime.utcnow().isoformat(),
                "latency_ms": 0.0,
                "last_error": err,
                "rows": int(len(df)),
            }
            return df
        df = _mock_ohlcv(limit)
        _source_status[(symbol, timeframe, exchange_name)] = "mock_fallback_live" if mode == "live" else "mock"
        _source_meta[(symbol, timeframe, exchange_name)] = {
            "last_fetch_utc": datetime.utcnow().isoformat(),
            "latency_ms": -1.0,
            "last_error": err or "dex adapter returned no data",
            "rows": int(len(df)),
        }
        return df

    # ── TTL REST cache ─────────────────────────────────────────────────────────
    cache_key = (symbol, timeframe, limit, exchange_name)
    if cache_key in _ohlcv_cache:
        return _ohlcv_cache[cache_key]
    try:
        t0 = time.perf_counter()
        ex = _ccxt_exchange(exchange_name)
        raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(raw, columns=["time", "open", "high", "low", "close", "volume"])
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True).dt.tz_localize(None)
        _ohlcv_cache[cache_key] = df
        _source_status[(symbol, timeframe, exchange_name)] = "live"
        _source_meta[(symbol, timeframe, exchange_name)] = {
            "last_fetch_utc": datetime.utcnow().isoformat(),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "last_error": "",
            "rows": int(len(df)),
        }
        logger.info("OHLCV live: %s %s %s (%d candles)", exchange_name, symbol, timeframe, len(df))
        return df
    except Exception as exc:
        logger.warning("ccxt OHLCV failed [%s %s %s]: %s -> using mock", exchange_name, symbol, timeframe, exc)
        df = _mock_ohlcv(limit)
        _ohlcv_cache[cache_key] = df
        _source_status[(symbol, timeframe, exchange_name)] = "mock_fallback_live" if mode == "live" else "mock"
        _source_meta[(symbol, timeframe, exchange_name)] = {
            "last_fetch_utc": datetime.utcnow().isoformat(),
            "latency_ms": -1.0,
            "last_error": str(exc),
            "rows": int(len(df)),
        }
        return df


def fetch_orderbook(
    symbol: str = "BTC/USDT",
    mid_price: Optional[float] = None,
    exchange_name: str = "binance",
    data_mode: str = "auto",
) -> Dict[str, List]:
    """Fetch order book from Binance with a 10-second TTL cache.
    Falls back to synthetic mock on error.
    """
    cache_key = (symbol, exchange_name)
    if cache_key in _book_cache:
        return _book_cache[cache_key]

    mode = str(data_mode).strip().lower()

    if mode == "mock":
        mid = mid_price or 62000.0
        result = _mock_orderbook(mid)
        _book_meta[cache_key] = {
            "last_fetch_utc": datetime.utcnow().isoformat(),
            "latency_ms": -1.0,
            "last_error": "",
            "source": "mock_forced",
        }
        _book_cache[cache_key] = result
        return result

    if is_dex_exchange(exchange_name):
        book, src, err = fetch_dex_orderbook(symbol, float(mid_price or 62000.0), exchange_name, data_mode=mode)
        if book is not None:
            _book_cache[cache_key] = book
            _book_meta[cache_key] = {
                "last_fetch_utc": datetime.utcnow().isoformat(),
                "latency_ms": 0.0,
                "last_error": err,
                "source": src,
            }
            return book
        mid = mid_price or 62000.0
        result = _mock_orderbook(mid)
        _book_cache[cache_key] = result
        _book_meta[cache_key] = {
            "last_fetch_utc": datetime.utcnow().isoformat(),
            "latency_ms": -1.0,
            "last_error": err or "dex adapter returned no orderbook",
            "source": "mock_fallback_live" if mode == "live" else "mock",
        }
        return result

    try:
        t0 = time.perf_counter()
        ex = _ccxt_exchange(exchange_name)
        book = ex.fetch_order_book(symbol, limit=20)
        result: Dict[str, List] = {"bids": book["bids"][:17], "asks": book["asks"][:17]}
        _book_cache[cache_key] = result
        _book_meta[cache_key] = {
            "last_fetch_utc": datetime.utcnow().isoformat(),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "last_error": "",
        }
        return result
    except Exception as exc:
        logger.warning("ccxt orderbook failed [%s %s]: %s -> using mock", exchange_name, symbol, exc)
        mid = mid_price or 62000.0
        result = _mock_orderbook(mid)
        _book_cache[cache_key] = result
        _book_meta[cache_key] = {
            "last_fetch_utc": datetime.utcnow().isoformat(),
            "latency_ms": -1.0,
            "last_error": str(exc),
            "source": "mock_fallback_live" if mode == "live" else "mock",
        }
        return result


def get_data_source(symbol: str = "BTC/USDT", timeframe: str = "1h", exchange_name: str = "binance") -> str:
    """Return 'live', 'mock', or 'unknown' for the last successful fetch."""
    return _source_status.get((symbol, timeframe, exchange_name), "unknown")


def get_data_meta(symbol: str = "BTC/USDT", timeframe: str = "1h", exchange_name: str = "binance") -> Dict[str, object]:
    return _source_meta.get((symbol, timeframe, exchange_name), {"last_fetch_utc": "", "latency_ms": -1.0, "last_error": "", "rows": 0})


def get_orderbook_meta(symbol: str = "BTC/USDT", exchange_name: str = "binance") -> Dict[str, object]:
    return _book_meta.get((symbol, exchange_name), {"last_fetch_utc": "", "latency_ms": -1.0, "last_error": ""})


# ── Public API (backward-compatible signatures) ───────────────────────────────

def generate_ohlcv(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    limit: int = 220,
    seed: int = 42,  # kept for compat, ignored when live data is available
    exchange_name: str = "binance",
    data_mode: str = "auto",
) -> pd.DataFrame:
    """Fetch OHLCV with real data + TTL cache, mock fallback."""
    return fetch_ohlcv(symbol, timeframe, limit, exchange_name, data_mode=data_mode)


def generate_orderbook(
    mid_price: float = 62000.0,
    symbol: str = "BTC/USDT",
    exchange_name: str = "binance",
    data_mode: str = "auto",
) -> Dict[str, List]:
    """Fetch order book with real data + TTL cache, mock fallback.
    mid_price is only used as fallback seed when ccxt fails.
    """
    return fetch_orderbook(symbol, mid_price, exchange_name, data_mode=data_mode)


# ── Mock generators (used as fallback) ────────────────────────────────────────

def _mock_ohlcv(limit: int = 220, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    now = datetime.utcnow()
    rows: List[dict] = []
    price = 62000.0
    for i in range(limit):
        t = now - timedelta(hours=limit - i)
        drift = random.uniform(-220, 220)
        o = price
        c = max(100.0, o + drift)
        h = max(o, c) + random.uniform(10, 120)
        l = min(o, c) - random.uniform(10, 120)
        v = random.uniform(80, 400)
        rows.append({"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v})
        price = c
    return pd.DataFrame(rows)


def _mock_orderbook(mid_price: float) -> Dict[str, List]:
    bids = [[round(mid_price - i * 5, 2), round(random.uniform(1.0, 8.0), 3)] for i in range(1, 18)]
    asks = [[round(mid_price + i * 5, 2), round(random.uniform(1.0, 8.0), 3)] for i in range(1, 18)]
    return {"bids": bids, "asks": asks}


def generate_human_trend_data() -> pd.DataFrame:
    base = [
        "Wireless earbuds",
        "Portable blender",
        "Action camera",
        "Gaming chair",
        "Smart ring",
        "Micro projector",
        "Fitness tracker",
        "Desk bike",
        "Robot vacuum",
    ]
    rows = []
    for item in base:
        rows.append(
            {
                "item": item,
                "volume": random.randint(5000, 55000),
                "growth_pct": round(random.uniform(-8.0, 35.0), 2),
                "sentiment": round(random.uniform(0.3, 0.9), 2),
            }
        )
    return pd.DataFrame(rows).sort_values("volume", ascending=False)
