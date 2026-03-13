from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class DoctorFinding:
    severity: str
    component: str
    issue: str
    recommendation: str
    priority: int


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def run_bot_doctor(metrics: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[DoctorFinding] = []

    decision_conf = _as_float(metrics.get("decision_conf"), 0.0)
    regime_conf = _as_float(metrics.get("regime_conf"), 0.0)
    depth_imbalance = abs(_as_float(metrics.get("depth_imbalance"), 0.0))
    drawdown = _as_float(metrics.get("drawdown"), 0.0)
    feed_age_s = _as_float(metrics.get("feed_age_s"), 0.0)
    live_interval_s = _as_float(metrics.get("live_interval_s"), 8.0)
    spread = _as_float(metrics.get("spread"), 0.0)
    decision = _as_str(metrics.get("decision"), "HOLD")

    if decision_conf < 0.55:
        findings.append(
            DoctorFinding(
                severity="warning",
                component="debate_engine",
                issue=f"Low decision confidence ({decision_conf:.0%})",
                recommendation="Reduce position size and wait for multi-signal confirmation.",
                priority=80,
            )
        )

    if regime_conf < 0.6 and decision != "HOLD":
        findings.append(
            DoctorFinding(
                severity="warning",
                component="regime_engine",
                issue=f"Trade proposed under weak regime confidence ({regime_conf:.0%})",
                recommendation="Require stronger regime confidence before executing non-HOLD decisions.",
                priority=75,
            )
        )

    if depth_imbalance > 0.35:
        findings.append(
            DoctorFinding(
                severity="warning",
                component="orderbook",
                issue=f"Large orderbook imbalance ({depth_imbalance:.2f})",
                recommendation="Tighten stops and watch for fast reversals/whipsaws.",
                priority=70,
            )
        )

    if live_interval_s > 0 and feed_age_s > (live_interval_s * 3.0):
        findings.append(
            DoctorFinding(
                severity="error",
                component="data_feed",
                issue=f"Data feed stale ({feed_age_s:.0f}s)",
                recommendation="Switch source/fallback and pause auto-execution until freshness recovers.",
                priority=95,
            )
        )

    if drawdown >= 0.08:
        findings.append(
            DoctorFinding(
                severity="error",
                component="risk_engine",
                issue=f"High drawdown ({drawdown:.1%})",
                recommendation="Trigger kill-switch conditions or reduce global exposure.",
                priority=100,
            )
        )

    if spread > 20:
        findings.append(
            DoctorFinding(
                severity="info",
                component="arbitrage_engine",
                issue=f"Potential arbitrage spread detected ({spread:.2f})",
                recommendation="Validate fees/slippage and route only if net spread remains positive.",
                priority=50,
            )
        )

    if not findings:
        findings.append(
            DoctorFinding(
                severity="info",
                component="system",
                issue="No critical anomalies detected",
                recommendation="Maintain current configuration and continue monitoring.",
                priority=10,
            )
        )

    findings_sorted = sorted(findings, key=lambda x: x.priority, reverse=True)
    health_score = max(0.0, 100.0 - (sum(f.priority for f in findings_sorted) / max(len(findings_sorted), 1)) * 0.35)

    return {
        "health_score": round(health_score, 1),
        "top_recommendation": findings_sorted[0].recommendation,
        "findings": [asdict(f) for f in findings_sorted],
    }
