from __future__ import annotations

from typing import Dict, Optional

import pandas as pd


def detect_trend(df: pd.DataFrame) -> str:
    ema50 = float(df["EMA50"].iloc[-1])
    ema200 = float(df["EMA200"].iloc[-1])
    if ema50 > ema200:
        return "BULLISH"
    if ema50 < ema200:
        return "BEARISH"
    return "RANGE"


def momentum_signal(df: pd.DataFrame) -> str:
    rsi = float(df["RSI"].iloc[-1])
    if rsi < 30:
        return "OVERSOLD"
    if rsi > 70:
        return "OVERBOUGHT"
    return "NEUTRAL"


def breakout_signal(df: pd.DataFrame, lookback: int = 20) -> str:
    last_close = float(df["close"].iloc[-1])
    recent_high = float(df["high"].tail(lookback).max())
    recent_low = float(df["low"].tail(lookback).min())
    if last_close >= recent_high:
        return "BREAKOUT_UP"
    if last_close <= recent_low:
        return "BREAKOUT_DOWN"
    return "NONE"


def volatility_state(df: pd.DataFrame) -> str:
    atr = float(df["ATR"].iloc[-1])
    mean_atr = float(df["ATR"].tail(80).mean())
    return "HIGH" if atr > mean_atr else "LOW"


def generate_trade(df: pd.DataFrame, sl_pct: float = 0.02, tp_pct: float = 0.04) -> Optional[Dict[str, float | str]]:
    trend = detect_trend(df)
    breakout = breakout_signal(df)
    price = float(df["close"].iloc[-1])

    if trend == "BULLISH" and breakout == "BREAKOUT_UP":
        entry = price
        stop = price * (1 - sl_pct)
        take = price * (1 + tp_pct)
        return {
            "type": "LONG",
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "take_profit": round(take, 2),
            "rr": round((take - entry) / max(1e-9, entry - stop), 2),
        }

    if trend == "BEARISH" and breakout == "BREAKOUT_DOWN":
        entry = price
        stop = price * (1 + sl_pct)
        take = price * (1 - tp_pct)
        return {
            "type": "SHORT",
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "take_profit": round(take, 2),
            "rr": round((entry - take) / max(1e-9, stop - entry), 2),
        }

    return None
