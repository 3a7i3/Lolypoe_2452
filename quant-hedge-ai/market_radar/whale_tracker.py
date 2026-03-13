"""Whale Tracker — enhanced whale detection with pattern analysis.

Extends the existing WhaleRadar from agents/whales/ with deeper
pattern recognition and accumulation/distribution tracking.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class WhaleActivity:
    """Single detected whale movement."""

    wallet: str
    symbol: str
    action: str  # "buy" | "sell" | "transfer"
    amount_usd: float
    timestamp: str
    platform: str = ""


@dataclass
class WhaleReport:
    """Aggregated whale intelligence for a scan cycle."""

    activities: list[WhaleActivity] = field(default_factory=list)
    accumulation_tokens: list[str] = field(default_factory=list)
    distribution_tokens: list[str] = field(default_factory=list)
    smart_money_flow: str = "neutral"  # "bullish" | "bearish" | "neutral"
    total_volume_usd: float = 0.0
    alert_count: int = 0
    sector_coverage: dict = field(default_factory=dict)  # sector -> coverage %


class WhaleTracker:
    """Tracks whale wallet activity and detects accumulation patterns.

    Builds on top of the existing WhaleRadar by adding:
    - Multi-wallet tracking across time
    - Accumulation vs distribution detection
    - Smart money flow direction
    """

    def __init__(
        self,
        threshold_usd: float = 500_000.0,
        top_wallets: int = 50,
    ) -> None:
        self.threshold_usd = threshold_usd
        self.top_wallets = top_wallets
        self._history: list[WhaleActivity] = []

    def scan(self, symbols: list[str]) -> WhaleReport:
        """Scan for whale activity across symbols.

        In simulation mode, generates synthetic whale movements.
        """
        activities = self._detect_movements(symbols)
        self._history.extend(activities)

        # Keep history bounded
        if len(self._history) > 10_000:
            self._history = self._history[-5_000:]

        report = self._build_report(activities)
        logger.info(
            "WhaleTracker: %d activities, flow=%s, accum=%s",
            len(activities),
            report.smart_money_flow,
            report.accumulation_tokens,
        )
        return report

    def get_alerts(self, report: WhaleReport) -> list[str]:
        """Convert whale report to alert strings compatible with DecisionEngine."""
        alerts: list[str] = []
        for a in report.activities:
            if a.amount_usd >= self.threshold_usd:
                tag = a.action.upper()
                alerts.append(f"WHALE_{tag}: {a.amount_usd / 1_000_000:.1f}M USD on {a.symbol}")
        if report.smart_money_flow == "bearish":
            alerts.append("SMART_MONEY_OUTFLOW: distribution detected")
        return alerts

    def detect_accumulation(self, symbol: str) -> dict:
        """Check if a symbol shows whale accumulation pattern.

        Returns pattern info based on recent history of the symbol.
        """
        sym_history = [h for h in self._history if h.symbol == symbol]
        if not sym_history:
            return {"pattern": "no_data", "confidence": 0.0, "buy_volume": 0.0, "sell_volume": 0.0}

        buy_vol = sum(a.amount_usd for a in sym_history if a.action == "buy")
        sell_vol = sum(a.amount_usd for a in sym_history if a.action == "sell")
        total = buy_vol + sell_vol

        if total == 0:
            return {"pattern": "inactive", "confidence": 0.0, "buy_volume": 0.0, "sell_volume": 0.0}

        buy_ratio = buy_vol / total
        if buy_ratio >= 0.7:
            pattern = "accumulation"
        elif buy_ratio <= 0.3:
            pattern = "distribution"
        else:
            pattern = "neutral"

        return {
            "pattern": pattern,
            "confidence": abs(buy_ratio - 0.5) * 2,
            "buy_volume": buy_vol,
            "sell_volume": sell_vol,
        }

    # ------------------------------------------------------------------

    def _detect_movements(self, symbols: list[str]) -> list[WhaleActivity]:
        """Detect whale movements. Simulated for now."""
        activities: list[WhaleActivity] = []
        for symbol in symbols:
            if random.random() < 0.3:  # 30% chance per symbol
                action = random.choice(["buy", "sell", "transfer"])
                amount = random.uniform(100_000, 5_000_000)
                activities.append(
                    WhaleActivity(
                        wallet=f"0x{random.randint(0, 0xFFFFFFFF):08x}",
                        symbol=symbol,
                        action=action,
                        amount_usd=amount,
                        timestamp="simulated",
                        platform=random.choice(["onchain", "cex"]),
                    )
                )
        return activities

    def _build_report(self, activities: list[WhaleActivity]) -> WhaleReport:
        """Aggregate activities into a whale report, enrich with sector coverage."""
        if not activities:
            return WhaleReport()

        total_buy = sum(a.amount_usd for a in activities if a.action == "buy")
        total_sell = sum(a.amount_usd for a in activities if a.action == "sell")
        total = total_buy + total_sell

        if total > 0:
            ratio = total_buy / total
            if ratio >= 0.65:
                flow = "bullish"
            elif ratio <= 0.35:
                flow = "bearish"
            else:
                flow = "neutral"
        else:
            flow = "neutral"

        # Identify accumulation/distribution tokens
        symbols_seen: dict[str, dict[str, float]] = {}
        sector_map: dict[str, str] = {}
        for a in activities:
            if a.symbol not in symbols_seen:
                symbols_seen[a.symbol] = {"buy": 0.0, "sell": 0.0}
            if a.action in ("buy", "sell"):
                symbols_seen[a.symbol][a.action] += a.amount_usd
            # sector extraction (simulate: first part of symbol before '_')
            sector = a.symbol.split('_')[0] if '_' in a.symbol else 'OTHER'
            sector_map[a.symbol] = sector

        accum = [s for s, v in symbols_seen.items() if v["buy"] > v["sell"] * 2]
        distrib = [s for s, v in symbols_seen.items() if v["sell"] > v["buy"] * 2]

        # Sector coverage calculation
        sector_totals: dict[str, float] = {}
        sector_whale: dict[str, float] = {}
        for sym, v in symbols_seen.items():
            sector = sector_map.get(sym, 'OTHER')
            total = v["buy"] + v["sell"]
            sector_totals[sector] = sector_totals.get(sector, 0.0) + total
            whale_amt = v["buy"] if sym in accum else v["sell"] if sym in distrib else 0.0
            sector_whale[sector] = sector_whale.get(sector, 0.0) + whale_amt

        sector_coverage = {}
        for sector in sector_totals:
            coverage = 0.0
            if sector_totals[sector] > 0:
                coverage = round(100.0 * sector_whale[sector] / sector_totals[sector], 2)
            sector_coverage[sector] = coverage

        return WhaleReport(
            activities=activities,
            accumulation_tokens=accum,
            distribution_tokens=distrib,
            smart_money_flow=flow,
            total_volume_usd=sum(a.amount_usd for a in activities),
            alert_count=sum(1 for a in activities if a.amount_usd >= self.threshold_usd),
            sector_coverage=sector_coverage,
        )
