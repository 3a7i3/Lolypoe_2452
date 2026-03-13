"""AI Market Radar — central orchestrator that unifies all scanning modules.

Combines: TokenScanner + WhaleTracker + SocialScanner + AnomalyDetector
into a single radar sweep that produces actionable opportunities.

Pipeline:
    MarketRadar.sweep()
        → TokenScanner  (new tokens)
        → WhaleTracker  (whale movements)
        → SocialScanner (social signals)
        → AnomalyDetector (market anomalies)
        → cross-reference & rank
        → return RadarReport (ready for Bot Doctor → Strategy AI → Sniper)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from market_radar.token_scanner import TokenScanner, TokenInfo
from market_radar.whale_tracker import WhaleTracker, WhaleReport
from market_radar.social_scanner import SocialScanner, SocialReport
from market_radar.anomaly_detector import AnomalyDetector, AnomalyReport

logger = logging.getLogger(__name__)


@dataclass
class Opportunity:
    """A ranked trading opportunity produced by the radar."""

    symbol: str
    score: float  # 0-100 composite score
    token_score: float = 0.0  # 0-10 from TokenScanner
    social_score: float = 0.0  # 0-10 from social sentiment
    whale_signal: str = "neutral"  # "accumulation" | "distribution" | "neutral"
    risk_level: str = "medium"  # "low" | "medium" | "high"
    sources: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


@dataclass
class RadarReport:
    """Complete output of a radar sweep cycle."""

    opportunities: list[Opportunity] = field(default_factory=list)
    whale_report: WhaleReport | None = None
    social_report: SocialReport | None = None
    anomaly_report: AnomalyReport | None = None
    tokens_scanned: int = 0
    tokens_passed_filters: int = 0
    risk_level: str = "normal"
    cycle: int = 0

    def top(self, n: int = 5) -> list[Opportunity]:
        """Return the top N opportunities by score."""
        return self.opportunities[:n]

    def as_dict(self) -> dict:
        """Summary dict for logging and dashboard display."""
        return {
            "opportunities_count": len(self.opportunities),
            "top_opportunities": [
                {"symbol": o.symbol, "score": round(o.score, 1), "risk": o.risk_level}
                for o in self.opportunities[:5]
            ],
            "tokens_scanned": self.tokens_scanned,
            "tokens_passed_filters": self.tokens_passed_filters,
            "whale_flow": self.whale_report.smart_money_flow if self.whale_report else "n/a",
            "social_sentiment": round(self.social_report.overall_sentiment, 2) if self.social_report else 0.0,
            "risk_level": self.risk_level,
            "anomaly_count": len(self.anomaly_report.anomalies) if self.anomaly_report else 0,
        }


class MarketRadar:
    """Central orchestrator — runs all scanners and produces ranked opportunities.

    Usage:
        radar = MarketRadar()
        report = radar.sweep(candles, features)
        for opp in report.top(5):
            if bot_doctor.validate(opp):
                sniper.execute(opp)
    """

    def __init__(
        self,
        min_liquidity_usd: float = 1_000.0,
        min_volume_usd: float = 500.0,
        whale_threshold_usd: float = 500_000.0,
        min_opportunity_score: float = 40.0,
    ) -> None:
        self.min_opportunity_score = min_opportunity_score
        self.token_scanner = TokenScanner(
            min_liquidity_usd=min_liquidity_usd,
            min_volume_usd=min_volume_usd,
        )
        self.whale_tracker = WhaleTracker(threshold_usd=whale_threshold_usd)
        self.social_scanner = SocialScanner()
        self.anomaly_detector = AnomalyDetector()
        self._cycle = 0

    def sweep(
        self,
        candles: list[dict],
        features: dict,
        whale_alerts: list[str] | None = None,
    ) -> RadarReport:
        """Execute a full radar sweep.

        Args:
            candles: OHLCV candle data from MarketScanner.
            features: Feature dict from FeatureEngineer.
            whale_alerts: Optional existing whale alerts (from WhaleRadar).

        Returns:
            RadarReport with ranked opportunities.
        """
        self._cycle += 1
        symbols = list({c["symbol"] for c in candles})

        # --- 1. Token scanning ---
        raw_tokens = self.token_scanner.scan()
        filtered_tokens = self.token_scanner.filter_tokens(raw_tokens)
        scored_tokens = self.token_scanner.score_all(filtered_tokens)

        # --- 2. Whale tracking ---
        whale_report = self.whale_tracker.scan(symbols)
        combined_whale_alerts = whale_alerts or []
        combined_whale_alerts.extend(self.whale_tracker.get_alerts(whale_report))

        # --- 3. Social scanning ---
        all_symbols = symbols + [t.symbol for t in scored_tokens[:10]]
        social_report = self.social_scanner.scan(all_symbols)

        # --- 4. Anomaly detection ---
        anomaly_report = self.anomaly_detector.detect(candles, features, combined_whale_alerts)

        # --- 5. Cross-reference and rank ---
        opportunities = self._build_opportunities(
            scored_tokens, whale_report, social_report, anomaly_report,
        )

        # Filter by minimum score
        opportunities = [o for o in opportunities if o.score >= self.min_opportunity_score]
        opportunities.sort(key=lambda o: o.score, reverse=True)

        report = RadarReport(
            opportunities=opportunities,
            whale_report=whale_report,
            social_report=social_report,
            anomaly_report=anomaly_report,
            tokens_scanned=len(raw_tokens),
            tokens_passed_filters=len(filtered_tokens),
            risk_level=anomaly_report.risk_level,
            cycle=self._cycle,
        )

        logger.info(
            "MarketRadar sweep #%d: %d opportunities (scanned=%d, filtered=%d, risk=%s)",
            self._cycle,
            len(opportunities),
            len(raw_tokens),
            len(filtered_tokens),
            anomaly_report.risk_level,
        )
        return report

    def _build_opportunities(
        self,
        tokens: list[TokenInfo],
        whale_report: WhaleReport,
        social_report: SocialReport,
        anomaly_report: AnomalyReport,
    ) -> list[Opportunity]:
        """Combine all signals into scored opportunities."""
        opportunities: list[Opportunity] = []

        for token in tokens:
            # Base score from token scanner (0-10 → 0-50)
            token_contrib = token.score * 5.0

            # Social boost (0-30)
            social_contrib = 0.0
            matching_signals = [s for s in social_report.signals if s.symbol == token.symbol]
            if matching_signals:
                avg_sentiment = sum(s.sentiment for s in matching_signals) / len(matching_signals)
                mentions = sum(s.mention_count for s in matching_signals)
                social_contrib = min(30.0, (avg_sentiment + 1.0) * 5.0 + min(mentions / 50, 10.0))
            social_score = social_contrib / 3.0  # normalized to 0-10

            # Whale signal (0-20)
            whale_signal = "neutral"
            whale_contrib = 0.0
            if token.symbol in whale_report.accumulation_tokens:
                whale_signal = "accumulation"
                whale_contrib = 20.0
            elif token.symbol in whale_report.distribution_tokens:
                whale_signal = "distribution"
                whale_contrib = -10.0

            # Risk penalty from anomalies
            risk_penalty = 0.0
            if anomaly_report.risk_level == "extreme":
                risk_penalty = 20.0
            elif anomaly_report.risk_level == "high":
                risk_penalty = 10.0
            elif anomaly_report.risk_level == "elevated":
                risk_penalty = 5.0

            composite = max(0.0, min(100.0, token_contrib + social_contrib + whale_contrib - risk_penalty))

            # Determine risk level
            if composite >= 70 and anomaly_report.risk_level in ("normal", "elevated"):
                risk = "low"
            elif composite >= 40:
                risk = "medium"
            else:
                risk = "high"

            flags: list[str] = []
            if token.age_seconds <= 300:
                flags.append("fresh_token")
            if token.whale_holders >= 2:
                flags.append("whale_interest")
            if matching_signals and any(s.trending for s in matching_signals):
                flags.append("trending")
            if anomaly_report.risk_level in ("high", "extreme"):
                flags.append("market_risk")

            opportunities.append(
                Opportunity(
                    symbol=token.symbol,
                    score=composite,
                    token_score=token.score,
                    social_score=social_score,
                    whale_signal=whale_signal,
                    risk_level=risk,
                    sources=[token.platform],
                    flags=flags,
                )
            )

        return opportunities
