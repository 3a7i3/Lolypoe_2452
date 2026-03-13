from __future__ import annotations

import pandas as pd

from v26.smart_chart import detect_structure, enrich_indicators, orderbook_depth


def _sample_df(size: int = 60) -> pd.DataFrame:
    t = pd.date_range("2026-01-01", periods=size, freq="h")
    base = pd.Series(range(size), dtype="float")
    close = 100.0 + base * 0.5
    open_ = close - 0.2
    high = close + 1.0
    low = close - 1.0
    vol = pd.Series([1000.0 + (i % 7) * 10.0 for i in range(size)])
    return pd.DataFrame(
        {
            "time": t,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": vol,
        }
    )


def _test_enrich_indicators() -> None:
    df = _sample_df()
    out = enrich_indicators(df, bb_dev=2.5)
    required_cols = ["EMA50", "EMA200", "RSI", "MACD", "MACD_SIGNAL", "ATR", "BBH", "BBL", "BBM"]
    missing = [c for c in required_cols if c not in out.columns]
    if missing:
        raise AssertionError(f"Missing indicator columns: {missing}")


def _test_detect_structure_neutral_case() -> None:
    # The 3rd candle is unchanged compared to the 2nd one and should stay neutral (NA).
    df = pd.DataFrame(
        {
            "high": [10.0, 11.0, 11.0, 12.0],
            "low": [8.0, 9.0, 9.0, 9.5],
        }
    )
    labels = detect_structure(df)
    expected = ["NA", "NA", "NA", "HH"]
    if labels != expected:
        raise AssertionError(f"Unexpected structure labels: {labels}, expected {expected}")


def _test_orderbook_depth() -> None:
    out = orderbook_depth({"bids": [[100.0, 3.0], [99.5, 2.0]], "asks": [[100.5, 1.0], [101.0, 2.0]]})
    if abs(out["bid_volume"] - 5.0) > 1e-9:
        raise AssertionError(f"Unexpected bid volume: {out['bid_volume']}")
    if abs(out["ask_volume"] - 3.0) > 1e-9:
        raise AssertionError(f"Unexpected ask volume: {out['ask_volume']}")
    if not (-1.0 <= out["imbalance"] <= 1.0):
        raise AssertionError(f"Imbalance out of bounds: {out['imbalance']}")


def main() -> None:
    _test_enrich_indicators()
    _test_detect_structure_neutral_case()
    _test_orderbook_depth()
    print("[OK] test_v30_smart_chart passed")


if __name__ == "__main__":
    main()
