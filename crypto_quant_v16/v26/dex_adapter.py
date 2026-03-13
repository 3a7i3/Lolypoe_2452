from __future__ import annotations

from datetime import datetime, timedelta
import random
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd


DEX_EXCHANGES = {"uniswap", "hyperliquid"}

OHLCVProvider = Callable[[str, str, int, str], Optional[pd.DataFrame]]
OrderbookProvider = Callable[[str, float, str], Optional[Dict[str, List]]]


_ohlcv_providers: Dict[str, OHLCVProvider] = {}
_orderbook_providers: Dict[str, OrderbookProvider] = {}


def _get_dex_route(exchange_name: str, symbol: str) -> Dict[str, str]:
    try:
        from v26.config import V26_CONFIG  # noqa: PLC0415
    except Exception:
        return {}
    routing = V26_CONFIG.get("dex_routing", {}) if isinstance(V26_CONFIG, dict) else {}
    if not isinstance(routing, dict):
        return {}
    ex_map = routing.get(str(exchange_name).lower(), {})
    if not isinstance(ex_map, dict):
        return {}
    row = ex_map.get(str(symbol), {})
    return row if isinstance(row, dict) else {}


def get_dex_route(exchange_name: str, symbol: str) -> Dict[str, str]:
    """Public accessor for configured DEX routing entries."""
    route = _get_dex_route(exchange_name, symbol)
    return dict(route) if isinstance(route, dict) else {}


def _base_symbol(symbol: str) -> str:
    left = str(symbol).split("/")[0].strip().upper()
    return left or "BTC"


def _symbol_aliases(symbol: str) -> set[str]:
    s = str(symbol).strip().upper()
    aliases = {s}
    if s == "BTC":
        aliases.add("WBTC")
    elif s == "WBTC":
        aliases.add("BTC")
    elif s == "ETH":
        aliases.add("WETH")
    elif s == "WETH":
        aliases.add("ETH")
    return aliases


def _fetch_uniswap_anchor_price(symbol: str) -> Optional[float]:
    try:
        import requests  # noqa: PLC0415
    except Exception:
        return None

    route = _get_dex_route("uniswap", symbol)
    pair_address = str(route.get("pair_address", "")).strip()
    chain = str(route.get("chain", "ethereum")).strip().lower() or "ethereum"
    if pair_address:
        try:
            resp = requests.get(
                f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{pair_address}",
                timeout=8,
            )
            if resp.status_code == 200:
                payload = resp.json() if resp.content else {}
                pair = payload.get("pair") if isinstance(payload, dict) else None
                if isinstance(pair, dict):
                    price = pair.get("priceUsd")
                    if price is not None:
                        px = float(price)
                        if px > 0:
                            return px
        except Exception:
            pass

    base_symbol = str(route.get("base_symbol", _base_symbol(symbol))).strip().upper() or _base_symbol(symbol)
    quote_symbol = str(route.get("quote_symbol", "USDT")).strip().upper() or "USDT"
    base_candidates = _symbol_aliases(base_symbol)
    quote_candidates = _symbol_aliases(quote_symbol)
    # Most liquid quote alternatives are acceptable for anchor pricing.
    if quote_symbol in {"USDT", "USDC"}:
        quote_candidates.update({"USDT", "USDC"})
    query = f"{base_symbol} {quote_symbol}"
    try:
        resp = requests.get(
            "https://api.dexscreener.com/latest/dex/search/",
            params={"q": query},
            timeout=8,
        )
        if resp.status_code != 200:
            return None
        payload = resp.json() if resp.content else {}
        pairs = payload.get("pairs") if isinstance(payload, dict) else None
        if not isinstance(pairs, list):
            return None
        for row in pairs:
            if not isinstance(row, dict):
                continue
            dex_id = str(row.get("dexId", "")).lower()
            if "uniswap" not in dex_id:
                continue
            row_chain = str(row.get("chainId", "")).strip().lower()
            if chain and row_chain and row_chain != chain:
                continue
            base_info = row.get("baseToken") if isinstance(row.get("baseToken"), dict) else {}
            quote_info = row.get("quoteToken") if isinstance(row.get("quoteToken"), dict) else {}
            base_row = str(base_info.get("symbol", "")).strip().upper()
            quote_row = str(quote_info.get("symbol", "")).strip().upper()
            if base_row and base_row not in base_candidates:
                continue
            if quote_row and quote_row not in quote_candidates:
                continue
            price = row.get("priceUsd")
            if price is None:
                continue
            px = float(price)
            if px > 0:
                return px
    except Exception:
        return None
    return None


def _fetch_hyperliquid_anchor_price(symbol: str) -> Optional[float]:
    try:
        import requests  # noqa: PLC0415
    except Exception:
        return None

    route = _get_dex_route("hyperliquid", symbol)
    coin = str(route.get("coin", _base_symbol(symbol))).strip().upper() or _base_symbol(symbol)
    try:
        resp = requests.post(
            "https://api.hyperliquid.xyz/info",
            json={"type": "metaAndAssetCtxs"},
            timeout=8,
        )
        if resp.status_code != 200:
            return None
        payload = resp.json() if resp.content else None
        if not isinstance(payload, list) or len(payload) < 2:
            return None
        meta = payload[0]
        ctxs = payload[1]
        if not isinstance(meta, dict) or not isinstance(ctxs, list):
            return None
        universes = meta.get("universe")
        if not isinstance(universes, list):
            return None

        for i, row in enumerate(universes):
            if not isinstance(row, dict):
                continue
            if str(row.get("name", "")).upper() != coin:
                continue
            if i >= len(ctxs) or not isinstance(ctxs[i], dict):
                continue
            px = float(ctxs[i].get("markPx", 0.0))
            if px > 0:
                return px
    except Exception:
        return None
    return None


def probe_dex_live_anchor(exchange_name: str, symbol: str) -> Tuple[Optional[float], str]:
    """Probe a best-effort live anchor and return (price, error_text)."""
    ex = str(exchange_name).strip().lower()
    if ex not in DEX_EXCHANGES:
        return None, f"unsupported dex exchange: {exchange_name}"

    if ex == "uniswap":
        px = _fetch_uniswap_anchor_price(symbol)
    elif ex == "hyperliquid":
        px = _fetch_hyperliquid_anchor_price(symbol)
    else:
        px = None

    if px is None or px <= 0:
        return None, "live anchor unavailable"
    return float(px), ""


def is_dex_exchange(exchange_name: str) -> bool:
    return str(exchange_name).strip().lower() in DEX_EXCHANGES


def register_ohlcv_provider(exchange_name: str, provider: OHLCVProvider) -> None:
    _ohlcv_providers[str(exchange_name).strip().lower()] = provider


def register_orderbook_provider(exchange_name: str, provider: OrderbookProvider) -> None:
    _orderbook_providers[str(exchange_name).strip().lower()] = provider


def _synthetic_ohlcv(limit: int = 220, seed: int = 42, anchor_price: float = 62000.0) -> pd.DataFrame:
    random.seed(seed)
    now = datetime.utcnow()
    rows: List[dict] = []
    price = float(anchor_price)
    for i in range(limit):
        t = now - timedelta(hours=limit - i)
        drift = random.uniform(-240, 240)
        o = price
        c = max(1.0, o + drift)
        h = max(o, c) + random.uniform(15, 140)
        l = min(o, c) - random.uniform(15, 140)
        v = random.uniform(60, 500)
        rows.append({"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v})
        price = c
    return pd.DataFrame(rows)


def _synthetic_orderbook(mid_price: float) -> Dict[str, List]:
    bids = [[round(mid_price - i * 4, 2), round(random.uniform(0.8, 9.0), 3)] for i in range(1, 18)]
    asks = [[round(mid_price + i * 4, 2), round(random.uniform(0.8, 9.0), 3)] for i in range(1, 18)]
    return {"bids": bids, "asks": asks}


def fetch_dex_ohlcv(
    symbol: str,
    timeframe: str,
    limit: int,
    exchange_name: str,
    data_mode: str = "auto",
) -> Tuple[Optional[pd.DataFrame], str, str]:
    """Return (df, source_label, error_text)."""
    ex = str(exchange_name).strip().lower()
    mode = str(data_mode).strip().lower()
    if mode == "mock":
        seed = abs(hash((symbol, timeframe, ex, "forced_mock"))) % 10_000
        return _synthetic_ohlcv(limit=limit, seed=seed), "dex_mock_forced", ""

    provider = _ohlcv_providers.get(ex)
    if provider is not None:
        try:
            df = provider(symbol, timeframe, limit, ex)
            if df is not None and not df.empty:
                return df, "dex_live", ""
        except Exception as exc:
            if mode == "live":
                return None, "dex_live", str(exc)

    # Built-in best-effort live anchors.
    anchor_price: Optional[float] = None
    if ex == "uniswap":
        anchor_price = _fetch_uniswap_anchor_price(symbol)
    elif ex == "hyperliquid":
        anchor_price = _fetch_hyperliquid_anchor_price(symbol)

    if anchor_price is not None and anchor_price > 0:
        seed = abs(hash((symbol, timeframe, ex, int(anchor_price * 100)))) % 10_000
        return _synthetic_ohlcv(limit=limit, seed=seed, anchor_price=float(anchor_price)), "dex_live", ""

    if mode == "live":
        return None, "dex_live", "live source unavailable"

    seed = abs(hash((symbol, timeframe, ex))) % 10_000
    return _synthetic_ohlcv(limit=limit, seed=seed), "dex_mock", ""


def fetch_dex_orderbook(
    symbol: str,
    mid_price: float,
    exchange_name: str,
    data_mode: str = "auto",
) -> Tuple[Optional[Dict[str, List]], str, str]:
    """Return (orderbook, source_label, error_text)."""
    ex = str(exchange_name).strip().lower()
    mode = str(data_mode).strip().lower()
    if mode == "mock":
        return _synthetic_orderbook(float(mid_price)), "dex_mock_forced", ""

    provider = _orderbook_providers.get(ex)
    if provider is not None:
        try:
            book = provider(symbol, float(mid_price), ex)
            if book is not None:
                return book, "dex_live", ""
        except Exception as exc:
            if mode == "live":
                return None, "dex_live", str(exc)

    # Orderbooks are not native on most DEX public endpoints, so we emulate depth
    # around the best-effort live anchor when available.
    anchor_price = float(mid_price)
    if ex == "uniswap":
        maybe = _fetch_uniswap_anchor_price(symbol)
        if maybe is not None and maybe > 0:
            anchor_price = float(maybe)
            return _synthetic_orderbook(anchor_price), "dex_live", ""
    elif ex == "hyperliquid":
        maybe = _fetch_hyperliquid_anchor_price(symbol)
        if maybe is not None and maybe > 0:
            anchor_price = float(maybe)
            return _synthetic_orderbook(anchor_price), "dex_live", ""

    if mode == "live":
        return None, "dex_live", "live source unavailable"

    return _synthetic_orderbook(float(mid_price)), "dex_mock", ""
