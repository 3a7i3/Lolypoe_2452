"""Bot Doctor Panel — displays risk diagnostics, corrections and health scores."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DoctorPanelReport:
    """Aggregated Bot Doctor state for one cycle."""

    health_score: float = 100.0
    top_recommendation: str = "System healthy"
    findings: list[dict] = field(default_factory=list)
    corrections_applied: list[str] = field(default_factory=list)
    corrections_total: int = 0
    blocked_trades: int = 0
    status: str = "healthy"  # "healthy" | "warning" | "critical"
    cycle: int = 0


class BotDoctorPanel:
    """Aggregates and renders Bot Doctor diagnostics across cycles.

    Consumes:
      - run_bot_doctor() output (health_score, findings)
      - apply_doctor_corrections_with_issues() output (corrections list)
    """

    def __init__(self) -> None:
        self._history: list[DoctorPanelReport] = []
        self._total_corrections = 0
        self._total_blocked = 0

    def record(
        self,
        cycle: int,
        doctor_result: dict,
        corrections: list[str] | None = None,
        blocked_trade: bool = False,
    ) -> DoctorPanelReport:
        """Record a Bot Doctor result for this cycle.

        Args:
            doctor_result: Output dict from run_bot_doctor() with keys
                           health_score, top_recommendation, findings.
            corrections: List of correction strings from apply_doctor_corrections_with_issues().
            blocked_trade: Whether a trade was blocked this cycle.
        """
        score = float(doctor_result.get("health_score", 100.0))
        corrections = corrections or []
        self._total_corrections += len(corrections)
        if blocked_trade:
            self._total_blocked += 1

        if score >= 80:
            status = "healthy"
        elif score >= 50:
            status = "warning"
        else:
            status = "critical"

        report = DoctorPanelReport(
            health_score=score,
            top_recommendation=doctor_result.get("top_recommendation", ""),
            findings=doctor_result.get("findings", []),
            corrections_applied=corrections,
            corrections_total=self._total_corrections,
            blocked_trades=self._total_blocked,
            status=status,
            cycle=cycle,
        )
        self._history.append(report)
        # Keep bounded
        if len(self._history) > 200:
            self._history = self._history[-100:]

        logger.info("BotDoctorPanel cycle %d: score=%.0f, status=%s", cycle, score, status)
        return report

    def show_diagnostics(self, report: DoctorPanelReport | None = None) -> None:
        """Print diagnostics to console (side-effect output for --dashboard mode)."""
        print(self.render(report))

    def avg_health(self, last_n: int = 10) -> float:
        """Average health score over the last N cycles."""
        window = self._history[-last_n:]
        if not window:
            return 100.0
        return sum(r.health_score for r in window) / len(window)

    def render(self, report: DoctorPanelReport | None = None) -> str:
        """Render Bot Doctor panel as formatted text."""
        r = report or (self._history[-1] if self._history else DoctorPanelReport())
        icon = "✅" if r.status == "healthy" else ("⚠️ " if r.status == "warning" else "🚨")
        avg = self.avg_health()

        lines = [
            "🩺 BOT DOCTOR DIAGNOSTICS",
            f"   {icon} Health Score : {r.health_score:.0f}/100  (avg-10: {avg:.0f})  |  Status: {r.status.upper()}",
            f"   Recommendation     : {r.top_recommendation or 'None'}",
            f"   Corrections Applied: {len(r.corrections_applied)} this cycle  |  {r.corrections_total} total",
            f"   Trades Blocked     : {r.blocked_trades} total",
        ]

        if r.findings:
            lines.append("   Findings:")
            for f in r.findings[:5]:  # Show top 5
                sev = f.get("severity", "info").upper()
                comp = f.get("component", "?")
                issue = f.get("issue", "")
                lines.append(f"      [{sev}] {comp}: {issue}")

        if r.corrections_applied:
            lines.append("   Corrections this cycle:")
            for c in r.corrections_applied[:3]:
                lines.append(f"      → {c}")

        return "\n".join(lines)
