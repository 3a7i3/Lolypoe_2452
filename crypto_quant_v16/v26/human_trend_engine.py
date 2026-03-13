from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Dict

import pandas as pd


CATEGORY_TO_ASSET = {
    "Wireless earbuds": "AAPL",
    "Gaming chair": "AMZN",
    "Action camera": "BTC",
    "Fitness tracker": "ETH",
    "Robot vacuum": "TSLA",
    "Micro projector": "SOL",
    "Smart ring": "NVDA",
    "Portable blender": "BNB",
    "Desk bike": "ADA",
}


def aggregate_by_source(base: pd.DataFrame, sources: list[str]) -> pd.DataFrame:
    rows = []
    for _, r in base.iterrows():
        for src in sources:
            rows.append(
                {
                    "source": src,
                    "item": r["item"],
                    "volume": int(r["volume"] * random.uniform(0.6, 1.2)),
                    "growth_pct": round(float(r["growth_pct"]) + random.uniform(-2.0, 3.0), 2),
                    "sentiment": round(min(1.0, max(0.0, float(r["sentiment"]) + random.uniform(-0.1, 0.1))), 2),
                }
            )
    return pd.DataFrame(rows)


def find_common_trends(source_df: pd.DataFrame) -> pd.DataFrame:
    grouped = source_df.groupby("item", as_index=False).agg(
        mentions=("source", "nunique"),
        total_volume=("volume", "sum"),
        avg_growth=("growth_pct", "mean"),
        avg_sentiment=("sentiment", "mean"),
    )
    grouped["linked_asset"] = grouped["item"].map(CATEGORY_TO_ASSET).fillna("BTC")
    grouped["trend_score"] = (
        grouped["mentions"] * 1.5
        + grouped["total_volume"] / grouped["total_volume"].max() * 6
        + grouped["avg_growth"] / 10
        + grouped["avg_sentiment"] * 2
    )
    return grouped.sort_values("trend_score", ascending=False)


def predict_next_products(common_df: pd.DataFrame, top_k: int = 6) -> pd.DataFrame:
    out = common_df.copy()
    out["next_score"] = out["trend_score"] * out["avg_sentiment"] * (1 + out["avg_growth"] / 100)
    return out.sort_values("next_score", ascending=False).head(top_k)


def source_sentiment_snapshot(source_df: pd.DataFrame) -> Dict[str, float]:
    data = source_df.groupby("source")["sentiment"].mean().to_dict()
    return {str(k): round(float(v), 3) for k, v in data.items()}


def build_trend_score_history(common_df: pd.DataFrame, steps: int = 18) -> pd.DataFrame:
    """Build a lightweight synthetic history from current trend scores.

    This keeps runtime cost low while providing a stable chart for trend momentum.
    """
    if common_df.empty:
        return pd.DataFrame(columns=["time", "item", "score"])

    now = datetime.utcnow()
    base = common_df[["item", "trend_score"]].copy()
    rows = []
    for i in range(steps):
        t = now - timedelta(minutes=(steps - i) * 10)
        noise_scale = 0.05 + (i / max(steps, 1)) * 0.04
        for _, r in base.iterrows():
            score = float(r["trend_score"]) * random.uniform(1.0 - noise_scale, 1.0 + noise_scale)
            rows.append({"time": t, "item": str(r["item"]), "score": max(0.0, score)})
    return pd.DataFrame(rows)
