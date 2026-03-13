from __future__ import annotations

from typing import Dict, List

import pandas as pd
from ta.momentum import rsi
from ta.trend import ema_indicator, macd, macd_signal
from ta.volatility import BollingerBands, average_true_range


def enrich_indicators(
    df: pd.DataFrame,
    ema_fast: int = 50,
    ema_slow: int = 200,
    rsi_period: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal_period: int = 9,
    atr_period: int = 14,
    bb_window: int = 20,
    bb_dev: float = 2.0,
) -> pd.DataFrame:
    out = df.copy()
    out["EMA50"] = ema_indicator(out["close"], window=int(ema_fast))
    out["EMA200"] = ema_indicator(out["close"], window=int(ema_slow))
    out["RSI"] = rsi(out["close"], window=int(rsi_period))
    out["MACD"] = macd(
        out["close"],
        window_slow=int(macd_slow),
        window_fast=int(macd_fast),
    )
    out["MACD_SIGNAL"] = macd_signal(
        out["close"],
        window_slow=int(macd_slow),
        window_fast=int(macd_fast),
        window_sign=int(macd_signal_period),
    )
    out["ATR"] = average_true_range(
        out["high"],
        out["low"],
        out["close"],
        window=int(atr_period),
    )

    bb_window_dev: int = max(1, int(round(bb_dev)))
    bb = BollingerBands(out["close"], window=int(bb_window), window_dev=bb_window_dev)
    out["BBH"] = bb.bollinger_hband()
    out["BBL"] = bb.bollinger_lband()
    out["BBM"] = bb.bollinger_mavg()
    return out


def detect_structure(df: pd.DataFrame) -> List[str]:
    labels: List[str] = ["NA", "NA"]
    for i in range(2, len(df)):
        prev_high = float(df["high"].iloc[i - 1])
        prev_low = float(df["low"].iloc[i - 1])
        high = float(df["high"].iloc[i])
        low = float(df["low"].iloc[i])

        if high > prev_high and low >= prev_low:
            labels.append("HH")
        elif low > prev_low and high <= prev_high:
            labels.append("HL")
        elif high < prev_high and low <= prev_low:
            labels.append("LH")
        elif low < prev_low and high >= prev_high:
            labels.append("LL")
        else:
            labels.append("NA")
    return labels


def detect_bos(df: pd.DataFrame, lookback: int = 20) -> List[str]:
    out: List[str] = []
    for i in range(len(df)):
        if i < lookback:
            out.append("NONE")
            continue
        window_h = df["high"].iloc[i - lookback:i].max()
        window_l = df["low"].iloc[i - lookback:i].min()
        c = df["close"].iloc[i]
        if c > window_h:
            out.append("BOS_UP")
        elif c < window_l:
            out.append("BOS_DOWN")
        else:
            out.append("NONE")
    return out


def detect_choch(df: pd.DataFrame, lookback: int = 12) -> List[str]:
    out: List[str] = []
    for i in range(len(df)):
        if i < lookback:
            out.append("NONE")
            continue
        if df["close"].iloc[i] > df["high"].iloc[i - lookback]:
            out.append("CHOCH_BULL")
        elif df["close"].iloc[i] < df["low"].iloc[i - lookback]:
            out.append("CHOCH_BEAR")
        else:
            out.append("NONE")
    return out


def detect_smart_money(df: pd.DataFrame) -> Dict[str, int]:
    body = (df["close"] - df["open"]).abs()
    wick = (df["high"] - df["low"]).abs()

    order_blocks = int((body > body.rolling(20, min_periods=1).mean() * 1.8).sum())
    fvg = int(((df["low"].shift(-1) > df["high"]) | (df["high"].shift(-1) < df["low"])).sum())
    sweeps = int((wick > wick.rolling(20, min_periods=1).mean() * 1.6).sum())

    return {"order_blocks": order_blocks, "fvg": fvg, "liquidity_sweeps": sweeps}


def detect_order_blocks_zones(df: pd.DataFrame, lookback: int = 40, max_zones: int = 8) -> List[Dict[str, float]]:
    """Return approximate order block zones as chart-ready rectangles.

    A zone is extracted from candles with abnormally large body inside a recent window.
    """
    if df.empty:
        return []
    body = (df["close"] - df["open"]).abs()
    avg = body.rolling(lookback, min_periods=1).mean()
    mask = body > (avg * 1.8)
    idx = list(df.index[mask])[-max_zones:]
    zones: List[Dict[str, float]] = []
    for i in idx:
        row = df.loc[i]
        zones.append(
            {
                "x0": row["time"],
                "x1": row["time"],
                "y0": float(min(row["open"], row["close"])),
                "y1": float(max(row["open"], row["close"])),
            }
        )
    return zones


def detect_fvg_zones(df: pd.DataFrame, max_zones: int = 8) -> List[Dict[str, float]]:
    """Return Fair Value Gap zones as chart-ready rectangles."""
    if len(df) < 3:
        return []
    zones: List[Dict[str, float]] = []
    for i in range(1, len(df) - 1):
        prev_h = float(df["high"].iloc[i - 1])
        prev_l = float(df["low"].iloc[i - 1])
        next_h = float(df["high"].iloc[i + 1])
        next_l = float(df["low"].iloc[i + 1])
        t = df["time"].iloc[i]

        # Bullish FVG: next candle low is above previous candle high.
        if next_l > prev_h:
            zones.append({"x0": t, "x1": t, "y0": prev_h, "y1": next_l})
        # Bearish FVG: next candle high is below previous candle low.
        elif next_h < prev_l:
            zones.append({"x0": t, "x1": t, "y0": next_h, "y1": prev_l})

    return zones[-max_zones:]


def orderbook_depth(orderbook: Dict[str, List[List[float]]]) -> Dict[str, float]:
    bids = orderbook.get("bids", [])
    asks = orderbook.get("asks", [])
    bid_volume = float(sum(v for _, v in bids))
    ask_volume = float(sum(v for _, v in asks))
    imbalance = (bid_volume - ask_volume) / max(1e-9, (bid_volume + ask_volume))
    return {"bid_volume": bid_volume, "ask_volume": ask_volume, "imbalance": imbalance}
