"""System Health — comprehensive health scoring across all system components."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class ComponentHealth:
    """Health state of a single system component."""

    name: str
    status: str = "ok"   # "ok" | "warning" | "error" | "unknown"
    score: float = 100.0  # 0-100
    message: str = ""


@dataclass
class SystemHealthReport:
    """Full system health report for one cycle."""

    components: list[ComponentHealth] = field(default_factory=list)
    overall_score: float = 100.0
    status: str = "healthy"  # "healthy" | "degraded" | "critical"
    uptime_s: float = 0.0
    cycle: int = 0
    timestamp: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    telegram_alerts_sent: int = 0


class SystemHealth:
    """Monitors overall system health by aggregating component states.

    Tracks: cycle speed, agent errors, radar signals, market risk,
    bot doctor status, and paper trading balance health.
    """

    def __init__(self) -> None:
        self._start_time = time.monotonic()
        self._cycle_times: list[float] = []
        self._last_cycle_start = time.monotonic()
        self._telegram_sent = 0
        self._errors: list[str] = []
        self._warnings: list[str] = []

    def record_cycle_start(self) -> None:
        self._last_cycle_start = time.monotonic()

    def record_cycle_end(self) -> None:
        elapsed = time.monotonic() - self._last_cycle_start
        self._cycle_times.append(elapsed)
        if len(self._cycle_times) > 50:
            self._cycle_times = self._cycle_times[-25:]

    def record_error(self, message: str) -> None:
        self._errors.append(message)
        if len(self._errors) > 100:
            self._errors = self._errors[-50:]

    def record_warning(self, message: str) -> None:
        self._warnings.append(message)
        if len(self._warnings) > 100:
            self._warnings = self._warnings[-50:]

    def record_telegram(self) -> None:
        self._telegram_sent += 1

    def evaluate(
        self,
        cycle: int,
        agent_errors: int = 0,
        doctor_score: float = 100.0,
        radar_risk: str = "normal",
        paper_balance: float = 100_000.0,
        starting_balance: float = 100_000.0,
    ) -> SystemHealthReport:
        """Calculate system health from current state."""
        components: list[ComponentHealth] = []

        # Cycle speed
        avg_cycle_s = sum(self._cycle_times) / len(self._cycle_times) if self._cycle_times else 0
        speed_score = 100.0 if avg_cycle_s < 5 else (80.0 if avg_cycle_s < 15 else 50.0)
        components.append(ComponentHealth(
            name="CycleSpeed",
            status="ok" if speed_score >= 80 else "warning",
            score=speed_score,
            message=f"{avg_cycle_s:.1f}s/cycle avg",
        ))

        # Agent health
        agent_score = max(0.0, 100.0 - agent_errors * 10)
        components.append(ComponentHealth(
            name="Agents",
            status="ok" if agent_errors == 0 else ("warning" if agent_errors < 3 else "error"),
            score=agent_score,
            message=f"{agent_errors} error(s)",
        ))

        # Bot Doctor
        doctor_status = "ok" if doctor_score >= 80 else ("warning" if doctor_score >= 50 else "error")
        components.append(ComponentHealth(
            name="BotDoctor",
            status=doctor_status,
            score=doctor_score,
            message=f"score={doctor_score:.0f}",
        ))

        # Market risk
        risk_scores = {"normal": 100.0, "elevated": 75.0, "high": 50.0, "extreme": 25.0}
        risk_score = risk_scores.get(radar_risk, 80.0)
        components.append(ComponentHealth(
            name="MarketRisk",
            status="ok" if risk_score >= 75 else ("warning" if risk_score >= 50 else "error"),
            score=risk_score,
            message=f"level={radar_risk}",
        ))

        # Paper trading P&L health
        if starting_balance > 0:
            pnl_pct = (paper_balance - starting_balance) / starting_balance
        else:
            pnl_pct = 0.0
        balance_score = 100.0 if pnl_pct >= 0 else max(0.0, 100.0 + pnl_pct * 200)
        components.append(ComponentHealth(
            name="PaperBalance",
            status="ok" if pnl_pct >= -0.05 else ("warning" if pnl_pct >= -0.15 else "error"),
            score=balance_score,
            message=f"pnl={pnl_pct:+.1%}",
        ))

        overall = sum(c.score for c in components) / len(components)
        if overall >= 80:
            status = "healthy"
        elif overall >= 50:
            status = "degraded"
        else:
            status = "critical"

        recent_errors = self._errors[-5:]
        recent_warnings = self._warnings[-5:]

        return SystemHealthReport(
            components=components,
            overall_score=overall,
            status=status,
            uptime_s=time.monotonic() - self._start_time,
            cycle=cycle,
            timestamp=datetime.now(timezone.utc).isoformat(),
            errors=recent_errors,
            warnings=recent_warnings,
            telegram_alerts_sent=self._telegram_sent,
        )

    def render(self, report: SystemHealthReport) -> str:
        """Render system health as formatted text."""
        icon = "✅" if report.status == "healthy" else ("⚠️ " if report.status == "degraded" else "🚨")
        uptime_min = report.uptime_s / 60
        lines = [
            "❤️  SYSTEM HEALTH",
            f"   {icon} Overall: {report.overall_score:.0f}/100  |  Status: {report.status.upper()}  |  "
            f"Uptime: {uptime_min:.1f}min  |  Telegram: {report.telegram_alerts_sent} sent",
        ]
        for c in report.components:
            c_icon = "✅" if c.status == "ok" else ("⚠️ " if c.status == "warning" else "❌")
            lines.append(f"   {c_icon} {c.name:<16s} {c.score:5.0f}/100  {c.message}")

        if report.errors:
            lines.append("   Errors:")
            for e in report.errors:
                lines.append(f"      ❌ {e}")
        if report.warnings:
            lines.append("   Warnings:")
            for w in report.warnings:
                lines.append(f"      ⚠️  {w}")
        return "\n".join(lines)
