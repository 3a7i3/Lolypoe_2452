"""Social Scanner — detects social media trends and sentiment signals."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SocialSignal:
    """A detected social trend or mention."""

    symbol: str
    source: str  # "twitter" | "telegram" | "reddit" | "discord"
    mention_count: int = 0
    sentiment: float = 0.0  # -1.0 (bearish) to 1.0 (bullish)
    trending: bool = False
    influencer_mentions: int = 0


@dataclass
class SocialReport:
    """Aggregated social intelligence for a scan cycle."""

    signals: list[SocialSignal] = field(default_factory=list)
    trending_tokens: list[str] = field(default_factory=list)
    bullish_tokens: list[str] = field(default_factory=list)
    bearish_tokens: list[str] = field(default_factory=list)
    overall_sentiment: float = 0.0  # -1.0 to 1.0


class SocialScanner:
    """Scans social media platforms for trading-relevant signals.

    Monitors Twitter/X, Telegram groups, Reddit, and Discord for:
    - Token mention spikes
    - Sentiment shifts
    - Influencer activity
    - Viral token discovery
    """

    SOURCES = ["twitter", "telegram", "reddit", "discord"]

    def __init__(
        self,
        min_mentions: int = 10,
        sentiment_threshold: float = 0.3,
        sources: list[str] | None = None,
    ) -> None:
        self.min_mentions = min_mentions
        self.sentiment_threshold = sentiment_threshold
        self.sources = sources or self.SOURCES
        self._previous_mentions: dict[str, int] = {}

    def scan(self, symbols: list[str]) -> SocialReport:
        """Scan social platforms for signals related to given symbols."""
        all_signals: list[SocialSignal] = []
        for source in self.sources:
            signals = self._scan_source(source, symbols)
            all_signals.extend(signals)

        report = self._build_report(all_signals)
        self._update_history(all_signals)

        logger.info(
            "SocialScanner: %d signals, trending=%s, sentiment=%.2f",
            len(all_signals),
            report.trending_tokens,
            report.overall_sentiment,
        )
        return report

    def detect_viral(self, symbol: str) -> dict:
        """Check if a symbol is going viral based on mention acceleration."""
        prev = self._previous_mentions.get(symbol, 0)
        current = prev  # In simulation, same as previous
        acceleration = (current - prev) / max(prev, 1) if prev > 0 else 0.0

        return {
            "symbol": symbol,
            "viral": acceleration > 2.0,
            "acceleration": acceleration,
            "previous_mentions": prev,
        }

    # ------------------------------------------------------------------

    def _scan_source(self, source: str, symbols: list[str]) -> list[SocialSignal]:
        """Scan a single source. Simulated for now."""
        signals: list[SocialSignal] = []
        for symbol in symbols:
            if random.random() < 0.4:  # 40% chance of mentions
                mentions = random.randint(1, 500)
                sentiment = random.uniform(-0.8, 0.8)
                signals.append(
                    SocialSignal(
                        symbol=symbol,
                        source=source,
                        mention_count=mentions,
                        sentiment=sentiment,
                        trending=mentions > 200,
                        influencer_mentions=random.randint(0, 5),
                    )
                )
        return signals

    def _build_report(self, signals: list[SocialSignal]) -> SocialReport:
        """Aggregate signals into a social report."""
        if not signals:
            return SocialReport()

        # Aggregate by symbol
        symbol_data: dict[str, dict] = {}
        for s in signals:
            if s.symbol not in symbol_data:
                symbol_data[s.symbol] = {"mentions": 0, "sentiment_sum": 0.0, "count": 0, "trending": False}
            symbol_data[s.symbol]["mentions"] += s.mention_count
            symbol_data[s.symbol]["sentiment_sum"] += s.sentiment
            symbol_data[s.symbol]["count"] += 1
            if s.trending:
                symbol_data[s.symbol]["trending"] = True

        trending = [sym for sym, d in symbol_data.items() if d["trending"] or d["mentions"] > 100]

        bullish = []
        bearish = []
        for sym, d in symbol_data.items():
            avg_sent = d["sentiment_sum"] / d["count"] if d["count"] else 0.0
            if avg_sent >= self.sentiment_threshold:
                bullish.append(sym)
            elif avg_sent <= -self.sentiment_threshold:
                bearish.append(sym)

        all_sentiments = [s.sentiment for s in signals]
        overall = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0.0

        return SocialReport(
            signals=signals,
            trending_tokens=trending,
            bullish_tokens=bullish,
            bearish_tokens=bearish,
            overall_sentiment=overall,
        )

    def _update_history(self, signals: list[SocialSignal]) -> None:
        """Update mention history for viral detection."""
        for s in signals:
            self._previous_mentions[s.symbol] = (
                self._previous_mentions.get(s.symbol, 0) + s.mention_count
            )
