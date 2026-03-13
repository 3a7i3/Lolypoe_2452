"""Whale Radar - Anomaly detection for large transaction activity."""
from __future__ import annotations

import random


class WhaleRadar:
    """Detects abnormal transaction patterns (synthetic for demo)."""

    def __init__(self, threshold_usd: float = 1_000_000) -> None:
        self.threshold = threshold_usd

    def scan(self, symbol: str, volume: float, price: float) -> dict:
        """
        Scan for whale activity.
        Returns dict with detected anomalies.
        """
        notional = volume * price

        alerts = []
        if notional > self.threshold:
            alerts.append(f"WHALE_BUY: {notional/1e6:.1f}M USD")

        # Synthetic detection: 20% chance of detecting large transfer
        if random.random() < 0.2:
            size = random.uniform(self.threshold, self.threshold * 5)
            direction = random.choice(["INFLOW_TO_EXCHANGE", "OUTFLOW_FROM_EXCHANGE"])
            alerts.append(f"{direction}: {size/1e6:.1f}M USD")

        return {
            "symbol": symbol,
            "alerts": alerts,
            "threat_level": "high" if len(alerts) >= 2 else ("medium" if alerts else "low"),
        }

    def analyze_pattern(self, transactions: list[dict]) -> dict:
        """Analyze historical transaction patterns."""
        if not transactions:
            return {"pattern": "insufficient_data", "anomaly_score": 0.0}

        large_txs = [t for t in transactions if float(t.get("amount", 0)) > self.threshold]
        anomaly_score = min(1.0, len(large_txs) / max(1, len(transactions)))

        return {
            "pattern": "whale_accumulation" if anomaly_score > 0.3 else "normal",
            "anomaly_score": round(anomaly_score, 4),
            "large_tx_count": len(large_txs),
        }
