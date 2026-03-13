from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd


@dataclass
class Vote:
    agent: str
    bias: str
    confidence: float
    reason: str


class TrendBot:
    def analyze(self, df: pd.DataFrame) -> Vote:
        ema50 = float(df["EMA50"].iloc[-1])
        ema200 = float(df["EMA200"].iloc[-1])
        if ema50 > ema200:
            return Vote("TrendBot", "LONG", 0.70, "EMA50 above EMA200")
        return Vote("TrendBot", "SHORT", 0.70, "EMA50 below EMA200")


class MomentumBot:
    def analyze(self, df: pd.DataFrame) -> Vote:
        rsi = float(df["RSI"].iloc[-1])
        if rsi < 30:
            return Vote("MomentumBot", "LONG", 0.60, "Market oversold")
        if rsi > 70:
            return Vote("MomentumBot", "SHORT", 0.60, "Market overbought")
        return Vote("MomentumBot", "NEUTRAL", 0.30, "Momentum neutral")


class StructureBot:
    def analyze(self, structure: List[str]) -> Vote:
        last = structure[-1] if structure else "NA"
        if last in {"HH", "HL"}:
            return Vote("StructureBot", "LONG", 0.80, "Bullish structure")
        if last in {"LH", "LL"}:
            return Vote("StructureBot", "SHORT", 0.80, "Bearish structure")
        return Vote("StructureBot", "NEUTRAL", 0.25, "No structure signal")


class VolatilityBot:
    def analyze(self, df: pd.DataFrame) -> Vote:
        atr = float(df["ATR"].iloc[-1])
        mean_atr = float(df["ATR"].tail(80).mean())
        if atr > mean_atr:
            return Vote("VolatilityBot", "TRADE", 0.60, "High volatility")
        return Vote("VolatilityBot", "WAIT", 0.60, "Low volatility")


class LiquidityBot:
    def analyze(self, depth: Dict[str, float]) -> Vote:
        if depth["bid_volume"] > depth["ask_volume"]:
            return Vote("LiquidityBot", "LONG", 0.65, "Buy pressure")
        return Vote("LiquidityBot", "SHORT", 0.65, "Sell pressure")


class DebateEngine:
    def __init__(self) -> None:
        self.trend = TrendBot()
        self.momentum = MomentumBot()
        self.structure = StructureBot()
        self.volatility = VolatilityBot()
        self.liquidity = LiquidityBot()

    def run(self, df: pd.DataFrame, structure: List[str], depth: Dict[str, float]) -> List[Vote]:
        return [
            self.trend.analyze(df),
            self.momentum.analyze(df),
            self.structure.analyze(structure),
            self.volatility.analyze(df),
            self.liquidity.analyze(depth),
        ]


def final_decision(votes: List[Vote]) -> Dict[str, float | str]:
    long_score = sum(v.confidence for v in votes if v.bias == "LONG")
    short_score = sum(v.confidence for v in votes if v.bias == "SHORT")

    if long_score > short_score:
        side = "LONG"
        conf = long_score / max(1e-9, long_score + short_score)
    elif short_score > long_score:
        side = "SHORT"
        conf = short_score / max(1e-9, long_score + short_score)
    else:
        side = "NO_TRADE"
        conf = 0.5

    return {"decision": side, "confidence": round(conf, 3), "long_score": round(long_score, 3), "short_score": round(short_score, 3)}
