"""V27.3 – Real-time Binance WebSocket kline feed with REST fallback.

Each (symbol, timeframe) pair gets a ``WsKlineFeed`` that:
- Streams `wss://stream.binance.com:9443/ws/<sym>@kline_<tf>` in a daemon thread
- Accumulates closed candles in a rolling deque(maxsize=220)
- Keeps the live, in-progress candle separately (never counted as "ready")
- Auto-reconnects with exponential backoff (2 s → 60 s max)
- Is Binance-only; Bybit falls back to REST automatically

Module-level public API
-----------------------
subscribe(symbol, timeframe)            - start/ensure feed, return WsKlineFeed
get_ws_ohlcv(symbol, timeframe, limit)  - DataFrame | None (None = use REST)
ws_status(symbol, timeframe)            - status string
ws_candles_ready(symbol, timeframe)     - int (# closed candles buffered)
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from collections import deque
from datetime import datetime
from typing import Dict, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# ── Binance URL helpers ────────────────────────────────────────────────────────

def _bn_symbol(symbol: str) -> str:
    """'BTC/USDT' → 'btcusdt'."""
    return symbol.replace("/", "").lower()


def _ws_url(symbol: str, timeframe: str) -> str:
    return f"wss://stream.binance.com:9443/ws/{_bn_symbol(symbol)}@kline_{timeframe}"


# ── Feed class ─────────────────────────────────────────────────────────────────

class WsKlineFeed:
    """Binance kline WebSocket stream for one (symbol, timeframe) pair."""

    MAXBUF = 220        # max closed candles kept
    READY_THRESHOLD = 10  # min closed candles before get_dataframe returns data

    def __init__(self, symbol: str, timeframe: str) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self._buf: deque[dict] = deque(maxlen=self.MAXBUF)
        self._live_candle: Optional[dict] = None
        self._lock = threading.Lock()
        self._status = "connecting"
        self._last_msg_ts: float = 0.0
        self._reconnect_delay: float = 2.0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background IO thread (idempotent)."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name=f"wsfeed_{_bn_symbol(self.symbol)}_{self.timeframe}",
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the feed thread to stop cleanly."""
        self._stop_event.set()

    def _run_loop(self) -> None:
        """Entry point for the daemon thread — owns its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while not self._stop_event.is_set():
            try:
                loop.run_until_complete(self._connect())
            except Exception as exc:
                logger.warning(
                    "WS %s %s: connection error (%s) – retry in %.1f s",
                    self.symbol, self.timeframe, exc, self._reconnect_delay,
                )
            with self._lock:
                self._status = "reconnecting"
            # honour stop_event during backoff sleep
            self._stop_event.wait(self._reconnect_delay)
            self._reconnect_delay = min(self._reconnect_delay * 1.8, 60.0)
        with self._lock:
            self._status = "disconnected"
        loop.close()

    async def _connect(self) -> None:
        """Open WS, stream messages until disconnect or stop_event."""
        try:
            import websockets  # noqa: PLC0415
        except ImportError:
            logger.error("websockets package not found – WS feed disabled")
            self._stop_event.set()
            return

        url = _ws_url(self.symbol, self.timeframe)
        with self._lock:
            self._status = "connecting"
        try:
            async with websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=30,
                open_timeout=15,
            ) as ws:
                with self._lock:
                    self._status = "live"
                    self._reconnect_delay = 2.0  # reset backoff
                logger.info("WS connected: %s", url)
                async for raw in ws:
                    if self._stop_event.is_set():
                        break
                    self._last_msg_ts = time.monotonic()
                    self._process(raw)
        except Exception:
            raise  # caught by _run_loop

    def _process(self, raw: "str | bytes") -> None:
        """Parse a kline message and update the buffer."""
        try:
            msg = json.loads(raw)
        except Exception:
            return
        # Support both stream format and combined-stream wrapped format
        k = msg.get("k") or (msg.get("data") or {}).get("k")
        if not isinstance(k, dict):
            return
        candle = {
            "time": datetime.utcfromtimestamp(int(k["t"]) / 1000),
            "open": float(k["o"]),
            "high": float(k["h"]),
            "low": float(k["l"]),
            "close": float(k["c"]),
            "volume": float(k["v"]),
        }
        with self._lock:
            if k.get("x"):  # x=True → candle is closed/confirmed
                self._buf.append(candle)
                self._live_candle = None
            else:
                self._live_candle = candle  # update in-progress candle

    # ── Public read interface ──────────────────────────────────────────────────

    @property
    def status(self) -> str:
        """'connecting'|'live'|'stale'|'reconnecting'|'disconnected'."""
        with self._lock:
            s = self._status
            if s == "live" and self._last_msg_ts > 0:
                # Mark stale if no message for > 90 s (e.g. 1m candles send ~every 1 s)
                if (time.monotonic() - self._last_msg_ts) > 90:
                    return "stale"
            return s

    def candles_ready(self) -> int:
        """Number of closed, confirmed candles in the buffer."""
        with self._lock:
            return len(self._buf)

    def get_dataframe(self, limit: int = 220) -> Optional[pd.DataFrame]:
        """Return closed candles (+ live candle appended) as a DataFrame.

        Returns ``None`` when not enough data is ready (< READY_THRESHOLD closed candles).
        """
        with self._lock:
            n_ready = len(self._buf)
            if n_ready < self.READY_THRESHOLD:
                return None
            rows = list(self._buf)
            live = self._live_candle

        if live is not None:
            rows = rows + [live]
        rows = rows[-limit:]
        return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])


# ── Module-level registry ──────────────────────────────────────────────────────

_feeds: Dict[Tuple[str, str], WsKlineFeed] = {}
_feeds_lock = threading.Lock()


def subscribe(symbol: str = "BTC/USDT", timeframe: str = "1h") -> WsKlineFeed:
    """Ensure a live WS feed for (symbol, timeframe) is running; return it.

    Idempotent – calling multiple times is safe.
    """
    key = (symbol, timeframe)
    with _feeds_lock:
        if key not in _feeds:
            feed = WsKlineFeed(symbol, timeframe)
            _feeds[key] = feed
            feed.start()
            logger.info("WS feed subscribed: %s %s", symbol, timeframe)
        return _feeds[key]


def get_ws_ohlcv(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    limit: int = 220,
) -> Optional[pd.DataFrame]:
    """Return a DataFrame from the WS buffer, or ``None`` if not ready.

    ``None`` signals the caller to fall back to REST (ccxt).
    Automatically subscribes/starts the feed on first call.
    """
    feed = subscribe(symbol, timeframe)
    return feed.get_dataframe(limit)


def ws_status(symbol: str = "BTC/USDT", timeframe: str = "1h") -> str:
    """Return the feed status string.

    ``'not_started'`` is returned when subscribe() has never been called.
    """
    key = (symbol, timeframe)
    with _feeds_lock:
        if key not in _feeds:
            return "not_started"
    return _feeds[key].status


def ws_candles_ready(symbol: str = "BTC/USDT", timeframe: str = "1h") -> int:
    """Return how many closed candles are buffered."""
    key = (symbol, timeframe)
    with _feeds_lock:
        if key not in _feeds:
            return 0
    return _feeds[key].candles_ready()
