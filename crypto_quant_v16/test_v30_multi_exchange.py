from __future__ import annotations

import os

from v26.data_simulator import generate_ohlcv, generate_orderbook, get_data_source


def _assert_not_empty_df(df) -> None:
    if df is None or df.empty:
        raise AssertionError("Expected non-empty DataFrame")


def _assert_orderbook(book) -> None:
    if not isinstance(book, dict):
        raise AssertionError("Orderbook must be a dict")
    if "bids" not in book or "asks" not in book:
        raise AssertionError("Orderbook must include bids/asks")
    if len(book["bids"]) == 0 or len(book["asks"]) == 0:
        raise AssertionError("Orderbook bids/asks must be non-empty")


def main() -> None:
    symbol = "BTC/USDT"
    timeframe = "1h"

    # CEX path
    cex = "mexc"
    df_cex = generate_ohlcv(symbol=symbol, timeframe=timeframe, limit=80, exchange_name=cex)
    _assert_not_empty_df(df_cex)
    src_cex = get_data_source(symbol, timeframe, cex)
    if src_cex not in {"live", "mock", "ws_live"}:
        raise AssertionError(f"Unexpected CEX source: {src_cex}")
    book_cex = generate_orderbook(mid_price=float(df_cex["close"].iloc[-1]), symbol=symbol, exchange_name=cex)
    _assert_orderbook(book_cex)

    # DEX path (adapter with synthetic fallback by default)
    dex = "uniswap"
    df_dex = generate_ohlcv(symbol=symbol, timeframe=timeframe, limit=80, exchange_name=dex)
    _assert_not_empty_df(df_dex)
    src_dex = get_data_source(symbol, timeframe, dex)
    if src_dex not in {"dex_live", "dex_mock", "mock"}:
        raise AssertionError(f"Unexpected DEX source: {src_dex}")
    book_dex = generate_orderbook(mid_price=float(df_dex["close"].iloc[-1]), symbol=symbol, exchange_name=dex)
    _assert_orderbook(book_dex)

    # Forced mock mode should always be available and explicit in source labels.
    df_mock_cex = generate_ohlcv(symbol=symbol, timeframe=timeframe, limit=40, exchange_name=cex, data_mode="mock")
    _assert_not_empty_df(df_mock_cex)
    src_mock_cex = get_data_source(symbol, timeframe, cex)
    if src_mock_cex not in {"mock_forced", "mock"}:
        raise AssertionError(f"Unexpected forced-mock CEX source: {src_mock_cex}")

    df_mock_dex = generate_ohlcv(symbol=symbol, timeframe=timeframe, limit=40, exchange_name=dex, data_mode="mock")
    _assert_not_empty_df(df_mock_dex)
    src_mock_dex = get_data_source(symbol, timeframe, dex)
    if src_mock_dex not in {"mock_forced", "dex_mock_forced", "dex_mock", "mock"}:
        raise AssertionError(f"Unexpected forced-mock DEX source: {src_mock_dex}")

    # Explicit live mode can be skipped in offline/CI mode to avoid flaky network dependency.
    offline = str(os.getenv("V30_OFFLINE_TESTS", "")).strip().lower() in {"1", "true", "yes", "on"}
    if not offline:
        df_live_dex = generate_ohlcv(symbol=symbol, timeframe=timeframe, limit=40, exchange_name=dex, data_mode="live")
        _assert_not_empty_df(df_live_dex)
        src_live_dex = get_data_source(symbol, timeframe, dex)
        if src_live_dex not in {"dex_live", "dex_mock", "mock_fallback_live", "mock"}:
            raise AssertionError(f"Unexpected live-mode DEX source: {src_live_dex}")
    else:
        print("[INFO] Skipping live-mode DEX probe (V30_OFFLINE_TESTS=1)")

    print("[OK] test_v30_multi_exchange passed")


if __name__ == "__main__":
    main()
