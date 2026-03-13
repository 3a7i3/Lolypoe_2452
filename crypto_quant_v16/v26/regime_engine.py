from __future__ import annotations

from typing import Dict

import pandas as pd


def detect_regime(df: pd.DataFrame) -> Dict[str, float | str]:
    ema50 = float(df["EMA50"].iloc[-1])
    ema200 = float(df["EMA200"].iloc[-1])
    atr = float(df["ATR"].iloc[-1])
    mean_atr = float(df["ATR"].tail(80).mean())

    if ema50 > ema200 and atr < mean_atr:
        return {"regime": "BULL_TREND", "confidence": 0.78}
    if ema50 < ema200 and atr < mean_atr:
        return {"regime": "BEAR_TREND", "confidence": 0.78}
    if atr > mean_atr * 1.08:
        return {"regime": "VOLATILE", "confidence": 0.74}
    return {"regime": "RANGE", "confidence": 0.66}


def choose_strategy(regime: str) -> str:
    mapping = {
        "BULL_TREND": "TrendFollowingStrategy",
        "BEAR_TREND": "ShortTrendStrategy",
        "RANGE": "MeanReversionStrategy",
        "VOLATILE": "BreakoutStrategy",
    }
    return mapping.get(regime, "NeutralStrategy")
