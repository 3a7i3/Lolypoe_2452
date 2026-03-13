"""Agent Monitor — tracks status, performance and health of all AI agents in the system."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Registry of all V9.1 agents by category
_AGENT_REGISTRY: dict[str, list[str]] = {
    "market": ["MarketScanner", "OrderFlowAnalyzer", "VolatilityDetector"],
    "intelligence": ["FeatureEngineer", "AdvancedRegimeDetector"],
    "whales": ["WhaleRadar", "WhaleTracker"],
    "strategy": ["StrategyGenerator", "GeneticOptimizer", "RLTrader"],
    "quant": ["BacktestLab", "MonteCarloSimulator", "PortfolioOptimizer"],
    "portfolio": ["PortfolioBrain"],
    "risk": ["RiskMonitor", "DrawdownGuard", "ExposureManager"],
    "execution": ["ExecutionEngine", "ArbitrageAgent", "LiquidityAnalyzer", "PaperTradingEngine"],
    "monitoring": ["PerformanceMonitor", "SystemMonitor", "CreatePromptAgent"],
    "radar": ["TokenScanner", "WhaleTracker", "SocialScanner", "AnomalyDetector"],
    "decision": ["DecisionEngine", "StrategyRanker"],
}


@dataclass
class AgentStatus:
    """Status snapshot for a single agent."""

    name: str
    category: str
    status: str = "active"  # "active" | "idle" | "error" | "disabled"
    last_run: str = ""
    cycles_completed: int = 0
    errors: int = 0
    latency_ms: float = 0.0
    last_output: str = ""


@dataclass
class AgentMonitorReport:
    """Full agent monitoring report for one cycle."""

    agents: list[AgentStatus] = field(default_factory=list)
    total_active: int = 0
    total_errors: int = 0
    errored_agents: list[str] = field(default_factory=list)
    cycle: int = 0


class AgentMonitor:
    """Tracks the status of all AI agents across cycles.

    Maintains per-agent state including error counts, cycle completions,
    and health status, producing a report each cycle.
    """

    def __init__(self) -> None:
        self._states: dict[str, AgentStatus] = {}
        self._cycle = 0
        # Initialize all known agents as active
        for category, names in _AGENT_REGISTRY.items():
            for name in names:
                self._states[name] = AgentStatus(name=name, category=category)

    def record_run(
        self,
        agent_name: str,
        latency_ms: float = 0.0,
        output_summary: str = "",
        error: bool = False,
    ) -> None:
        """Record that an agent completed a run this cycle."""
        if agent_name not in self._states:
            self._states[agent_name] = AgentStatus(name=agent_name, category="unknown")

        s = self._states[agent_name]
        s.cycles_completed += 1
        s.latency_ms = latency_ms
        s.last_run = datetime.now(timezone.utc).isoformat()
        s.last_output = output_summary

        if error:
            s.errors += 1
            s.status = "error"
        else:
            s.status = "active"

    def tick(self, cycle: int) -> AgentMonitorReport:
        """Generate status report for current cycle."""
        self._cycle = cycle
        agents = sorted(self._states.values(), key=lambda a: (a.category, a.name))
        errored = [a.name for a in agents if a.status == "error"]

        return AgentMonitorReport(
            agents=agents,
            total_active=sum(1 for a in agents if a.status == "active"),
            total_errors=sum(a.errors for a in agents),
            errored_agents=errored,
            cycle=cycle,
        )

    def render(self, report: AgentMonitorReport) -> str:
        """Render agent monitor as formatted text."""
        lines = [
            "🤖 AI AGENTS MONITOR",
            f"   Active: {report.total_active}/{len(report.agents)}  |  "
            f"Total Errors: {report.total_errors}  |  "
            f"Cycle: {report.cycle}",
        ]
        current_cat = ""
        for a in report.agents:
            if a.category != current_cat:
                current_cat = a.category
                lines.append(f"   [{current_cat.upper()}]")
            icon = "✅" if a.status == "active" else ("❌" if a.status == "error" else "💤")
            err_tag = f" [{a.errors}err]" if a.errors > 0 else ""
            lines.append(f"      {icon} {a.name:<28s} cycles={a.cycles_completed}{err_tag}")
        if report.errored_agents:
            lines.append(f"   ⚠️  Errored: {', '.join(report.errored_agents)}")
        return "\n".join(lines)
