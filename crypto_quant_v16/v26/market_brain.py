from __future__ import annotations

from typing import Dict, List

import pandas as pd


def trend_ai(df: pd.DataFrame) -> tuple[str, float]:
    return ("BULLISH", 0.70) if float(df["EMA50"].iloc[-1]) > float(df["EMA200"].iloc[-1]) else ("BEARISH", 0.70)


def sentiment_ai(sentiment_score: float) -> tuple[str, float]:
    if sentiment_score > 0.6:
        return ("BULLISH", 0.60)
    if sentiment_score < 0.4:
        return ("BEARISH", 0.60)
    return ("NEUTRAL", 0.50)


def liquidity_ai(bid_volume: float, ask_volume: float) -> tuple[str, float]:
    return (("BUY_PRESSURE", 0.65) if bid_volume > ask_volume else ("SELL_PRESSURE", 0.65))


def volatility_ai(df: pd.DataFrame) -> tuple[str, float]:
    atr = float(df["ATR"].iloc[-1])
    mean_atr = float(df["ATR"].tail(80).mean())
    return ("HIGH_VOL", 0.60) if atr > mean_atr else ("LOW_VOL", 0.60)


def fuse_market_state(results: List[tuple[str, float]]) -> Dict[str, float | str]:
    bullish = sum(w for label, w in results if "BULLISH" in label or "BUY_PRESSURE" in label)
    bearish = sum(w for label, w in results if "BEARISH" in label or "SELL_PRESSURE" in label)
    if bullish > bearish:
        state = "BULLISH_MARKET"
        conf = bullish / max(1e-9, bullish + bearish)
    elif bearish > bullish:
        state = "BEARISH_MARKET"
        conf = bearish / max(1e-9, bullish + bearish)
    else:
        state = "NEUTRAL_MARKET"
        conf = 0.5
    return {"state": state, "confidence": round(conf, 3), "bullish_score": round(bullish, 3), "bearish_score": round(bearish, 3)}
