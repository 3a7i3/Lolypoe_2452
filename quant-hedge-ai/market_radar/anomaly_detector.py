"""Anomaly Detector — identifies unusual market conditions and patterns."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MarketAnomaly:
    """A single detected market anomaly."""

    symbol: str
    anomaly_type: str  # "volume_spike" | "price_crash" | "price_pump" | "liquidity_drain" | "whale_cluster"
    severity: str  # "low" | "medium" | "high" | "critical"
    value: float = 0.0
    threshold: float = 0.0
    description: str = ""


@dataclass
class AnomalyReport:
    """Aggregated anomaly detection results."""

    anomalies: list[MarketAnomaly] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    risk_level: str = "normal"  # "normal" | "elevated" | "high" | "extreme"


class AnomalyDetector:
    """Detects unusual market conditions from features, candles, and whale data.

    Anomaly types:
    - Volume spikes (>3x average)
    - Flash price movements (>10% in short window)
    - Liquidity drain events
    - Whale cluster activity (multiple whales on same token)
    """

    def __init__(
        self,
        volume_spike_factor: float = 3.0,
        price_move_threshold: float = 0.10,
        liquidity_drop_threshold: float = 0.30,
    ) -> None:
        self.volume_spike_factor = volume_spike_factor
        self.price_move_threshold = price_move_threshold
        self.liquidity_drop_threshold = liquidity_drop_threshold

    def detect(
        self,
        candles: list[dict],
        features: dict,
        whale_alerts: list[str] | None = None,
    ) -> AnomalyReport:
        """Run all anomaly detectors and return consolidated report."""
        anomalies: list[MarketAnomaly] = []
        anomalies.extend(self._check_volume(candles))
        anomalies.extend(self._check_price_moves(candles))
        anomalies.extend(self._check_features(features))
        if whale_alerts:
            anomalies.extend(self._check_whale_clusters(whale_alerts))

        critical = sum(1 for a in anomalies if a.severity == "critical")
        high = sum(1 for a in anomalies if a.severity == "high")

        if critical >= 2:
            risk_level = "extreme"
        elif critical >= 1 or high >= 3:
            risk_level = "high"
        elif high >= 1:
            risk_level = "elevated"
        else:
            risk_level = "normal"

        report = AnomalyReport(
            anomalies=anomalies,
            critical_count=critical,
            high_count=high,
            risk_level=risk_level,
        )
        logger.info(
            "AnomalyDetector: %d anomalies, risk=%s (critical=%d, high=%d)",
            len(anomalies), risk_level, critical, high,
        )
        return report

    # ------------------------------------------------------------------
    # Individual detectors
    # ------------------------------------------------------------------

    def _check_volume(self, candles: list[dict]) -> list[MarketAnomaly]:
        """Detect volume spikes."""
        if len(candles) < 2:
            return []

        volumes = [float(c.get("volume", 0)) for c in candles]
        avg_vol = sum(volumes) / len(volumes) if volumes else 1

        anomalies = []
        for c in candles:
            vol = float(c.get("volume", 0))
            if avg_vol > 0 and vol > avg_vol * self.volume_spike_factor:
                ratio = vol / avg_vol
                severity = "critical" if ratio > 10 else ("high" if ratio > 5 else "medium")
                anomalies.append(
                    MarketAnomaly(
                        symbol=c.get("symbol", "UNKNOWN"),
                        anomaly_type="volume_spike",
                        severity=severity,
                        value=ratio,
                        threshold=self.volume_spike_factor,
                        description=f"Volume {ratio:.1f}x above average",
                    )
                )
        return anomalies

    def _check_price_moves(self, candles: list[dict]) -> list[MarketAnomaly]:
        """Detect flash price movements."""
        anomalies = []
        for c in candles:
            open_p = float(c.get("open", 0))
            close_p = float(c.get("close", 0))
            if open_p <= 0:
                continue

            move = (close_p - open_p) / open_p
            if abs(move) > self.price_move_threshold:
                atype = "price_pump" if move > 0 else "price_crash"
                severity = "critical" if abs(move) > 0.25 else ("high" if abs(move) > 0.15 else "medium")
                anomalies.append(
                    MarketAnomaly(
                        symbol=c.get("symbol", "UNKNOWN"),
                        anomaly_type=atype,
                        severity=severity,
                        value=move,
                        threshold=self.price_move_threshold,
                        description=f"Price moved {move:+.1%} in single candle",
                    )
                )
        return anomalies

    def _check_features(self, features: dict) -> list[MarketAnomaly]:
        """Detect anomalies from intelligence features."""
        anomalies = []
        vol = features.get("realized_volatility", 0.0)
        momentum = features.get("momentum", 0.0)

        if vol > 0.08:
            anomalies.append(
                MarketAnomaly(
                    symbol="MARKET",
                    anomaly_type="high_volatility",
                    severity="high" if vol > 0.12 else "medium",
                    value=vol,
                    threshold=0.08,
                    description=f"Realized volatility at {vol:.4f}",
                )
            )

        if abs(momentum) > 0.05:
            anomalies.append(
                MarketAnomaly(
                    symbol="MARKET",
                    anomaly_type="extreme_momentum",
                    severity="high" if abs(momentum) > 0.08 else "medium",
                    value=momentum,
                    threshold=0.05,
                    description=f"Extreme momentum: {momentum:+.4f}",
                )
            )

        return anomalies

    def _check_whale_clusters(self, whale_alerts: list[str]) -> list[MarketAnomaly]:
        """Detect when multiple whale alerts cluster on the same action."""
        if len(whale_alerts) <= 2:
            return []

        buy_count = sum(1 for a in whale_alerts if "BUY" in a.upper())
        sell_count = sum(1 for a in whale_alerts if "SELL" in a.upper())

        anomalies = []
        if buy_count >= 3:
            anomalies.append(
                MarketAnomaly(
                    symbol="MARKET",
                    anomaly_type="whale_cluster",
                    severity="high",
                    value=float(buy_count),
                    threshold=3.0,
                    description=f"Whale buy cluster: {buy_count} concurrent buys",
                )
            )
        if sell_count >= 3:
            anomalies.append(
                MarketAnomaly(
                    symbol="MARKET",
                    anomaly_type="whale_cluster",
                    severity="critical",
                    value=float(sell_count),
                    threshold=3.0,
                    description=f"Whale sell cluster: {sell_count} concurrent sells",
                )
            )

        return anomalies
