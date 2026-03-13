"""Liquidity Flow Analyzer - detects capital rotation between sectors/tokens.

Consumes whale alerts + market candle data to build a flow map showing
where money is moving. Produces opportunity signals when capital
concentrates in a sector.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Sector classification for common tokens
_SECTOR_MAP: dict[str, str] = {
    "BTCUSDT": "BTC",
    "ETHUSDT": "ETH_L1",
    "SOLUSDT": "SOL_L1",
    "BNBUSDT": "BNB_L1",
    "AVAXUSDT": "ALT_L1",
    "MATICUSDT": "ALT_L1",
    "ADAUSDT": "ALT_L1",
    "DOTUSDT": "ALT_L1",
    "LINKUSDT": "DEFI",
    "UNIUSDT": "DEFI",
    "AAVEUSDT": "DEFI",
    "MKRUSDT": "DEFI",
    "SHIBUSDT": "MEMECOINS",
    "DOGEUSDT": "MEMECOINS",
    "PEPEUSDT": "MEMECOINS",
    "BONKUSDT": "MEMECOINS",
    "FLOKIUSDT": "MEMECOINS",
    "WIFUSDT": "MEMECOINS",
    "RENDERUSDT": "AI_TOKENS",
    "FETUSDT": "AI_TOKENS",
    "AGIXUSDT": "AI_TOKENS",
    "TAOUSDT": "AI_TOKENS",
    "NEARUSDT": "AI_TOKENS",
}


def _classify_sector(symbol: str) -> str:
    """Map a symbol to its sector. Unknown symbols go to ALTCOINS."""
    return _SECTOR_MAP.get(symbol.upper(), "ALTCOINS")


@dataclass
class SectorFlow:
    """Capital flow metrics for a single sector."""

    sector: str
    volume_usd: float = 0.0
    whale_flow_usd: float = 0.0
    token_count: int = 0
    avg_change_pct: float = 0.0
    momentum_score: float = 0.0

    @property
    def total_flow(self) -> float:
        return self.volume_usd + self.whale_flow_usd

    @property
    def opportunity_score(self) -> float:
        """0-100 score based on capital concentration."""
        base = min(50.0, self.whale_flow_usd / 1_000_000) if self.whale_flow_usd > 0 else 0
        momentum_bonus = max(0, min(30.0, self.momentum_score * 30))
        diversity_bonus = min(20.0, self.token_count * 5.0)
        return min(100.0, base + momentum_bonus + diversity_bonus)


@dataclass
class FlowReport:
    """Complete liquidity flow analysis for one cycle."""

    cycle: int = 0
    sector_flows: list[SectorFlow] = field(default_factory=list)
    top_sector: str = "none"
    top_sector_score: float = 0.0
    total_volume_usd: float = 0.0
    total_whale_flow_usd: float = 0.0
    parsed_whale_alerts_usd: float = 0.0
    whale_unmapped_usd: float = 0.0
    whale_mapping_coverage: float = 1.0
    whale_consistency_gap_usd: float = 0.0
    capital_concentration: float = 0.0  # 0-1, high = concentrated
    regime: str = "unknown"
    opportunities: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "cycle": self.cycle,
            "top_sector": self.top_sector,
            "top_sector_score": round(self.top_sector_score, 1),
            "total_volume_usd": round(self.total_volume_usd, 0),
            "total_whale_flow_usd": round(self.total_whale_flow_usd, 0),
            "parsed_whale_alerts_usd": round(self.parsed_whale_alerts_usd, 0),
            "whale_unmapped_usd": round(self.whale_unmapped_usd, 0),
            "whale_mapping_coverage": round(self.whale_mapping_coverage, 3),
            "whale_consistency_gap_usd": round(self.whale_consistency_gap_usd, 0),
            "capital_concentration": round(self.capital_concentration, 3),
            "sectors_active": len(self.sector_flows),
            "opportunities": len(self.opportunities),
            "regime": self.regime,
            "sector_details": [
                {
                    "sector": sf.sector,
                    "volume_usd": round(sf.volume_usd, 0),
                    "whale_flow_usd": round(sf.whale_flow_usd, 0),
                    "score": round(sf.opportunity_score, 1),
                    "momentum": round(sf.momentum_score, 3),
                }
                for sf in self.sector_flows[:8]
            ],
            "multi_sector_opportunities": getattr(self, "multi_sector_opps", []),
        }


class LiquidityFlowMap:
    """Analyzes capital rotation between market sectors.

    Combines candle volume data with whale alerts to build a sector-level
    flow map and generate opportunity signals.
    """

    def __init__(self, opportunity_threshold: float = 40.0) -> None:
        self.opportunity_threshold = opportunity_threshold
        self._history: list[FlowReport] = []

    def analyze(
        self,
        candles: list[dict],
        whale_alerts: list[str],
        regime: str = "unknown",
        cycle: int = 0,
    ) -> FlowReport:
        """Build a flow map from candle data + whale alerts.

        Args:
            candles: Market candles with symbol, close, volume, open.
            whale_alerts: Whale alert strings from WhaleRadar.
            regime: Current market regime.
            cycle: Current cycle number.
        """
        # --- 1. Aggregate volume by sector ---
        sector_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"volume": 0.0, "whale_flow": 0.0, "changes": [], "tokens": set()}
        )

        # ...existing code...
        for candle in candles:
            symbol = str(candle.get("symbol", ""))
            close = float(candle.get("close", 0))
            open_price = float(candle.get("open", close))
            volume = float(candle.get("volume", 0))
            notional = volume * close

            sector = _SECTOR_MAP.get(symbol, "OTHER")
            sector_data[sector]["volume"] += notional
            sector_data[sector]["tokens"].add(symbol)

            if open_price > 0:
                change_pct = (close - open_price) / open_price
                sector_data[sector]["changes"].append(change_pct)

        # --- 2. Parse whale alerts for sector flows ---
        parsed_whale_total = 0.0
        unmapped_whale_total = 0.0

        for alert in whale_alerts:
            alert_upper = alert.upper()
            whale_usd = self._parse_whale_amount(alert)
            parsed_whale_total += whale_usd
            mapped = False

            # Try exact full-symbol match first (e.g. "BTCUSDT" in alert)
            for symbol, sector in _SECTOR_MAP.items():
                if symbol in alert_upper:
                    sector_data[sector]["whale_flow"] += whale_usd
                    mapped = True
                    # ...existing code...
                    break

            # Try word-boundary token match (avoids "ETH" matching "SETH")
            if not mapped:
                for symbol, sector in _SECTOR_MAP.items():
                    token = symbol.replace("USDT", "")
                    if re.search(rf"\b{re.escape(token)}\b", alert_upper):
                        sector_data[sector]["whale_flow"] += whale_usd
                        mapped = True
                        # ...existing code...
                        break

            # Fallback for common tickers with word boundary
            if not mapped:
                for token, sect in (("BTC", "BTC"), ("ETH", "ETH_L1"), ("SOL", "SOL_L1")):
                    if re.search(rf"\b{token}\b", alert_upper):
                        sector_data[sect]["whale_flow"] += whale_usd
                        mapped = True
                        # ...existing code...
                        break

            # Last resort: keyword-based sector inference (word boundary)
            if whale_usd > 0 and not mapped:
                inferred = "OTHER"
                # Priorité STABLE/STABLECOIN et EXCHANGE pour STABLECOINS
                if re.search(r"\bSTABLECOIN\b", alert_upper):
                    inferred = "STABLECOINS"
                elif re.search(r"\bSTABLE\b", alert_upper):
                    inferred = "STABLECOINS"
                elif re.search(r"EXCHANGE", alert_upper):
                    inferred = "STABLECOINS"
                    sector_data[inferred]["whale_flow"] += whale_usd
                    unmapped_whale_total += whale_usd
                    # ...existing code...
                    continue
                else:
                    import json
                    import os
                    kw_path = os.path.join(os.path.dirname(__file__), "sector_keywords.json")
                    with open(kw_path, "r", encoding="utf-8") as f:
                        kw_map = json.load(f)
                    # Liste de priorité configurable
                    priority_path = os.path.join(os.path.dirname(__file__), "sector_priority.json")
                    with open(priority_path, "r", encoding="utf-8") as pf:
                        priority = json.load(pf)
                    found = None
                    for kw in priority:
                        if kw in kw_map and re.search(rf"\b{kw}\b", alert_upper):
                            found = kw
                            break
                    if found:
                        inferred = kw_map[found]
                    else:
                        # Fallback: premier mot-clé trouvé
                        for kw, sect in kw_map.items():
                            if re.search(rf"\b{kw}\b", alert_upper):
                                inferred = sect
                                break
                sector_data[inferred]["whale_flow"] += whale_usd
                unmapped_whale_total += whale_usd

        # --- 3. Build SectorFlow objects ---
        flows: list[SectorFlow] = []
        total_vol = 0.0
        total_whale = 0.0

        # Ensure STABLECOINS sector is included if whale flow mapped there
        if "STABLECOINS" not in sector_data and any(
            re.search(r"\bEXCHANGE\b", alert.upper()) for alert in whale_alerts
        ):
            sector_data["STABLECOINS"] = {"volume": 0.0, "whale_flow": 0.0, "changes": [], "tokens": set()}

        for sector, data in sector_data.items():
            changes = data["changes"]
            avg_change = sum(changes) / len(changes) if changes else 0.0
            momentum = max(-1.0, min(1.0, avg_change * 10))

            sf = SectorFlow(
                sector=sector,
                volume_usd=data["volume"],
                whale_flow_usd=data["whale_flow"],
                token_count=len(data["tokens"]),
                avg_change_pct=avg_change,
                momentum_score=momentum,
            )
            flows.append(sf)
            total_vol += data["volume"]
            total_whale += data["whale_flow"]

        flows.sort(key=lambda f: f.opportunity_score, reverse=True)

        # --- 4. Capital concentration (Herfindahl-like) ---
        concentration = 0.0
        if total_vol > 0:
            shares = [(f.volume_usd / total_vol) for f in flows]
            concentration = sum(s * s for s in shares)

        # --- 5. Generate opportunities ---
        opportunities = []
        for sf in flows:
            if sf.opportunity_score >= self.opportunity_threshold:
                opportunities.append({
                    "sector": sf.sector,
                    "score": round(sf.opportunity_score, 1),
                    "volume_usd": round(sf.volume_usd, 0),
                    "whale_flow_usd": round(sf.whale_flow_usd, 0),
                    "momentum": round(sf.momentum_score, 3),
                })

        top = flows[0] if flows else SectorFlow(sector="none")
        report = FlowReport(
            cycle=cycle,
            sector_flows=flows,
            top_sector=top.sector,
            top_sector_score=top.opportunity_score,
            total_volume_usd=total_vol,
            total_whale_flow_usd=total_whale,
            parsed_whale_alerts_usd=parsed_whale_total,
            whale_unmapped_usd=unmapped_whale_total,
            whale_mapping_coverage=((total_whale - unmapped_whale_total) / parsed_whale_total) if parsed_whale_total > 0 else 1.0,
            whale_consistency_gap_usd=abs(parsed_whale_total - total_whale),
            capital_concentration=concentration,
            regime=regime,
            opportunities=opportunities,
        )

        self._history.append(report)
        # ...existing code...
        if len(self._history) > 200:
            self._history = self._history[-100:]

        logger.info(
            "FlowMap cycle %d: %d sectors, top=%s(%.0f), concentration=%.3f",
            cycle, len(flows), top.sector, top.opportunity_score, concentration,
        )
        return report

    def render(self, report: FlowReport) -> str:
        """Render flow report as text."""
        lines = [
            f"💧 LIQUIDITY FLOW MAP",
            f"   Regime: {report.regime}  |  Concentration: {report.capital_concentration:.1%}",
            f"   Total Volume: ${report.total_volume_usd:,.0f}  |  "
            f"Whale Flow: ${report.total_whale_flow_usd:,.0f}",
            f"   Whale Parse: alerts=${report.parsed_whale_alerts_usd:,.0f}  |  "
            f"unmapped=${report.whale_unmapped_usd:,.0f}  |  "
            f"coverage={report.whale_mapping_coverage:.1%}  |  "
            f"gap=${report.whale_consistency_gap_usd:,.0f}",
            f"   Sectors Active: {len(report.sector_flows)}  |  "
            f"Opportunities: {len(report.opportunities)}",
            "",
        ]

        for sf in report.sector_flows[:8]:
            icon = "^" if sf.momentum_score > 0.1 else ("v" if sf.momentum_score < -0.1 else "=")
            lines.append(
                f"   {icon} {sf.sector:<12s}  vol=${sf.volume_usd:>12,.0f}  "
                f"whale=${sf.whale_flow_usd:>10,.0f}  "
                f"score={sf.opportunity_score:5.1f}  "
                f"tokens={sf.token_count}"
            )

        if report.opportunities:
            lines.append("")
            lines.append(f"   Opportunities (score >= {self.opportunity_threshold}):")
            for opp in report.opportunities[:5]:
                lines.append(
                    f"      {opp['sector']:<12s} score={opp['score']:5.1f}  "
                    f"momentum={opp['momentum']:+.3f}"
                )

        return "\n".join(lines) + "\n"

    @staticmethod
    def _parse_whale_amount(alert: str) -> float:
        """Extract USD amount from whale alert string."""
        match = re.search(r"(?<!\w)(\d+(?:,\d{3})*(?:\.\d+)?)\s*([KMB])?\s*USD\b", alert, re.IGNORECASE)
        if match:
            val = float(match.group(1).replace(",", ""))
            unit = (match.group(2) or "").upper()
            if unit == "K":
                val *= 1_000
            elif unit == "M":
                val *= 1_000_000
            elif unit == "B":
                val *= 1_000_000_000
            return val
        return 0.0
