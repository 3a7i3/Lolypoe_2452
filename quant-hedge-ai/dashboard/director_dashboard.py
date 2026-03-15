"""Director Super Dashboard — central control center for the AI Hedge Fund system.

Aggregates all monitoring subsystems into a single cockpit view:
  - AI Agents Monitor
  - Bot Doctor Diagnostics
  - Strategy Performance
  - Active Trades
  - Market Radar Signals
  - System Health
  - Telegram Alerts

Usage in the main loop:
    director = DirectorDashboard()
    director.update(cycle, data_dict)
    print(director.render())

Standalone:
    python dashboard/director_dashboard.py
    python main_v91.py --dashboard
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Allow running standalone: python dashboard/director_dashboard.py
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard.agent_monitor import AgentMonitor, AgentMonitorReport
from dashboard.bot_doctor_panel import BotDoctorPanel, DoctorPanelReport
from dashboard.trade_monitor import TradeMonitor, TradeMonitorReport
from dashboard.system_health import SystemHealth, SystemHealthReport

logger = logging.getLogger(__name__)

_SEP = "=" * 80
_SEP_THIN = "-" * 80


@dataclass
class DirectorSnapshot:
    """Complete state snapshot for one dashboard cycle."""

    cycle: int = 0
    agent_report: AgentMonitorReport | None = None
    doctor_report: DoctorPanelReport | None = None
    trade_report: TradeMonitorReport | None = None
    health_report: SystemHealthReport | None = None
    radar_summary: dict = field(default_factory=dict)
    strategy_factory_summary: dict = field(default_factory=dict)
    market_regime: str = "unknown"
    whale_flow: str = "neutral"
    strategy_type: str = "unknown"
    top_strategy: dict | None = None
    telegram_alerts: list[str] = field(default_factory=list)
    evo_summary: dict = field(default_factory=dict)
    flow_summary: dict = field(default_factory=dict)


class DirectorDashboard:
    """Central control cockpit for the AI Hedge Fund Trading System.

    Manages all monitoring subsystems and renders a unified full report.
    Acts as the single source of truth for system status at any cycle.
    """

    def __init__(self, starting_balance: float = 100_000.0) -> None:
        self.agent_monitor = AgentMonitor()
        self.doctor_panel = BotDoctorPanel()
        self.trade_monitor = TradeMonitor(starting_balance=starting_balance)
        self.system_health = SystemHealth()
        self._snapshots: list[DirectorSnapshot] = []
        self._telegram_alerts: list[str] = []

    def update(
        self,
        cycle: int,
        *,
        # Agent data
        agent_errors: int = 0,
        # Bot Doctor data
        doctor_result: dict | None = None,
        corrections: list[str] | None = None,
        blocked_trade: bool = False,
        # Trade data
        paper_state: dict | None = None,
        trade_action: str = "HOLD",
        trade_symbol: str = "",
        trade_size: float = 0.0,
        trade_price: float = 0.0,
        # Radar data
        radar_summary: dict | None = None,
        strategy_factory_summary: dict | None = None,
        # Market intelligence
        market_regime: str = "unknown",
        whale_alerts: list[str] | None = None,
        whale_flow: str = "neutral",
        suggested_strategy_type: str = "unknown",
        best_strategy: dict | None = None,
        # Telegram
        telegram_message: str = "",
        # Evolution + Flow
        evo_summary: dict | None = None,
        flow_summary: dict | None = None,
    ) -> DirectorSnapshot:
        """Push new data into all monitoring subsystems and generate a snapshot."""
        self.system_health.record_cycle_start()

        # --- Agent Monitor ---
        if agent_errors > 0:
            self.agent_monitor.record_run("system", error=True, output_summary=f"{agent_errors} errors")
        agent_report = self.agent_monitor.tick(cycle)

        # --- Bot Doctor ---
        doctor_result = doctor_result or {"health_score": 100.0, "top_recommendation": "", "findings": []}
        doctor_report = self.doctor_panel.record(
            cycle, doctor_result, corrections=corrections or [], blocked_trade=blocked_trade,
        )

        # --- Trade Monitor ---
        if paper_state:
            self.trade_monitor.record_paper_state(paper_state, cycle)
        if trade_action in ("BUY", "SELL") and trade_symbol:
            self.trade_monitor.record_trade(
                symbol=trade_symbol,
                action=trade_action,
                size=trade_size,
                price=trade_price,
                cycle=cycle,
            )
        trade_report = self.trade_monitor.tick(cycle, paper_state)

        # --- System Health ---
        radar_risk = (radar_summary or {}).get("risk_level", "normal")
        health_report = self.system_health.evaluate(
            cycle=cycle,
            agent_errors=agent_errors,
            doctor_score=doctor_report.health_score,
            radar_risk=radar_risk,
            paper_balance=trade_report.balance,
        )
        self.system_health.record_cycle_end()

        # --- Telegram alerts ---
        if telegram_message:
            self._telegram_alerts.append(telegram_message)
            self.system_health.record_telegram()
        if len(self._telegram_alerts) > 50:
            self._telegram_alerts = self._telegram_alerts[-25:]

        snapshot = DirectorSnapshot(
            cycle=cycle,
            agent_report=agent_report,
            doctor_report=doctor_report,
            trade_report=trade_report,
            health_report=health_report,
            radar_summary=radar_summary or {},
            strategy_factory_summary=strategy_factory_summary or {},
            market_regime=market_regime,
            whale_flow=whale_flow,
            strategy_type=suggested_strategy_type,
            top_strategy=best_strategy,
            telegram_alerts=list(self._telegram_alerts[-5:]),
            evo_summary=evo_summary or {},
            flow_summary=flow_summary or {},
        )
        self._snapshots.append(snapshot)
        if len(self._snapshots) > 200:
            self._snapshots = self._snapshots[-100:]

        logger.info(
            "DirectorDashboard cycle %d: health=%.0f, doctor=%.0f, regime=%s",
            cycle, health_report.overall_score, doctor_report.health_score, market_regime,
        )
        return snapshot

    def render(self, snapshot: DirectorSnapshot | None = None) -> str:
        """Render the full Director Dashboard as a text report."""
        s = snapshot or (self._snapshots[-1] if self._snapshots else DirectorSnapshot())

        lines = [
            "",
            _SEP,
            f"🎯  DIRECTOR SUPER DASHBOARD — CYCLE {s.cycle}",
            _SEP,
        ]

        # --- Market Radar section ---
        r = s.radar_summary
        lines += [
            "",
            f"📡 MARKET RADAR",
            f"   Regime   : {s.market_regime.upper():<20s}  Strategy Type : {s.strategy_type}",
            f"   Whale Flow: {s.whale_flow:<20s}  Risk Level    : {r.get('risk_level', 'n/a')}",
            f"   Opportunities: {r.get('opportunities_count', 0)}  |  "
            f"Social Sentiment: {r.get('social_sentiment', 0.0):+.2f}  |  "
            f"Tokens Scanned: {r.get('tokens_scanned', 0)}",
        ]
        top_opps = r.get("top_opportunities", [])
        if top_opps:
            top_str = "  ".join(f"{o['symbol']}({o['score']:.0f})" for o in top_opps[:3])
            lines.append(f"   Top Signals : {top_str}")

        sf = s.strategy_factory_summary
        if sf:
            lines += [
                "",
                "🏭 STRATEGY FACTORY",
                f"   Regime   : {sf.get('regime', 'unknown')}",
                f"   Generated: {sf.get('generated_count', 0)}  |  Backtested: {sf.get('backtested_count', 0)}  |  Filtered: {sf.get('filtered_count', 0)}",
                f"   Approved : {sf.get('approved_count', 0)}  |  Blocked   : {sf.get('blocked_count', 0)}",
                f"   Memory   : loaded={sf.get('memory_loaded_count', 0)}  saved={sf.get('memory_saved_count', 0)}",
            ]

        # --- Best Strategy section ---
        lines.append("")
        if s.top_strategy:
            strat = s.top_strategy.get("strategy", {})
            lines += [
                "📊 STRATEGY PERFORMANCE",
                f"   Best: {strat.get('entry_indicator', '?')} → {strat.get('exit_indicator', '?')}  "
                f"period={strat.get('period', '?')}",
                f"   Sharpe: {s.top_strategy.get('sharpe', 0.0):.4f}  |  "
                f"Drawdown: {s.top_strategy.get('drawdown', 0.0):.2%}  |  "
                f"Win Rate: {s.top_strategy.get('win_rate', 0.0):.1%}  |  "
                f"PnL: {s.top_strategy.get('pnl', 0.0):.4f}",
            ]
        else:
            lines += ["📊 STRATEGY PERFORMANCE", "   No active strategy"]

        # --- Subsystem panels ---
        lines.append("")
        lines.append(_SEP_THIN)

        # --- AI Evolution Lab ---
        ev = s.evo_summary
        if ev:
            lines += [
                "\U0001f9ec AI EVOLUTION LAB",
                f"   Generation  : {ev.get('generation', 0)}  |  Regime: {ev.get('regime', 'unknown')}",
                f"   Candidates  : {ev.get('candidates', 0)} "
                f"({ev.get('from_memory', 0)} memory + "
                f"{ev.get('candidates', 0) - ev.get('from_memory', 0)} fresh)",
                f"   Best Sharpe : {ev.get('best_sharpe', 0):.4f}  |  "
                f"Avg Sharpe: {ev.get('avg_sharpe', 0):.4f}",
                f"   Best Strat  : {ev.get('best_strategy_name', 'none')}",
                f"   Saved       : {ev.get('saved', 0)}  |  "
                f"Doctor Blocked: {ev.get('doctor_blocked', 0)}",
            ]
            lines.append(_SEP_THIN)

        # --- Liquidity Flow Map ---
        fl = s.flow_summary
        if fl:
            # Envoi d'une alerte Telegram si couverture faible (<50%)
            try:
                sector_details = fl.get('sector_details', [])
                mapped_sectors = [sd['sector'] for sd in sector_details if sd['whale_flow_usd'] > 0]
                all_sectors = set(sd['sector'] for sd in sector_details)
                coverage_pct = (len(mapped_sectors) / len(all_sectors)) * 100 if all_sectors else 0
                if coverage_pct < 50:
                    # Import dynamique pour éviter dépendance si non utilisé
                    import sys
                    sys.path.append(str(Path(__file__).resolve().parent.parent.parent / 'crypto_quant_v16' / 'v26'))
                    try:
                        from telegram_alerts import send_alert
                        send_alert(
                            level="warning",
                            key="sector_coverage",
                            message=f"Couverture sectorielle faible : {coverage_pct:.1f}%\nSecteurs mappés : {', '.join(mapped_sectors) if mapped_sectors else 'aucun'}"
                        )
                    except Exception as e:
                        logger.warning(f"Erreur envoi alerte Telegram : {e}")
            except Exception as e:
                logger.warning(f"Erreur calcul couverture sectorielle : {e}")
            lines += [
                "\U0001f4a7 LIQUIDITY FLOW MAP",
                f"   Top Sector  : {fl.get('top_sector', 'none')} "
                f"(score={fl.get('top_sector_score', 0):.1f})",
                f"   Total Volume: ${fl.get('total_volume_usd', 0):,.0f}  |  "
                f"Whale Flow: ${fl.get('total_whale_flow_usd', 0):,.0f}",
                f"   Whale Parse : alerts=${fl.get('parsed_whale_alerts_usd', 0):,.0f}  |  "
                f"unmapped=${fl.get('whale_unmapped_usd', 0):,.0f}  |  "
                f"coverage={fl.get('whale_mapping_coverage', 0.0):.1%}  |  "
                f"gap=${fl.get('whale_consistency_gap_usd', 0):,.0f}",
                f"   Concentration: {fl.get('capital_concentration', 0):.1%}  |  "
                f"Sectors: {fl.get('sectors_active', 0)}  |  "
                f"Opportunities: {fl.get('opportunities', 0)}",
            ]
            # Rapport de couverture sectorielle personnalisé
            sector_details = fl.get('sector_details', [])
            mapped_sectors = [sd['sector'] for sd in sector_details if sd['whale_flow_usd'] > 0]
            all_sectors = set(sd['sector'] for sd in sector_details)
            unmapped_sectors = [s for s in all_sectors if s not in mapped_sectors]
            coverage_pct = (len(mapped_sectors) / len(all_sectors)) * 100 if all_sectors else 0
            # Couleur ANSI
            if coverage_pct >= 80:
                color = '\033[92m'  # vert
                symbol = '✅'
            elif coverage_pct >= 50:
                color = '\033[93m'  # orange
                symbol = '⚠️'
            else:
                color = '\033[91m'  # rouge
                symbol = '❌'
            endc = '\033[0m'
            # Barre ASCII (pour compatibilité test)
            bar_len = 20
            filled = int(bar_len * coverage_pct / 100)
            bar = '[' + '#' * filled + '-' * (bar_len - filled) + f'] {coverage_pct:.1f}% {symbol}'
            # Affichage multi-lignes pour les secteurs (compatibilité test)
            mapped_str = ', '.join(mapped_sectors) if mapped_sectors else 'aucun'
            unmapped_str = ', '.join(unmapped_sectors) if unmapped_sectors else 'aucun'
            lines += [
                f"Couverture sectorielle : {bar}",
                f"Secteurs mappés : {mapped_str}",
                f"Secteurs non mappés : {unmapped_str}",
            ]
            lines.append(_SEP_THIN)

        if s.agent_report:
            lines.append(self.agent_monitor.render(s.agent_report))

        lines.append(_SEP_THIN)
        if s.doctor_report:
            lines.append(self.doctor_panel.render(s.doctor_report))

        lines.append(_SEP_THIN)
        if s.trade_report:
            lines.append(self.trade_monitor.render(s.trade_report))

        lines.append(_SEP_THIN)
        if s.health_report:
            lines.append(self.system_health.render(s.health_report))

        # --- Telegram alerts ---
        lines.append(_SEP_THIN)
        lines.append("📡 TELEGRAM ALERTS")
        if s.telegram_alerts:
            for alert in s.telegram_alerts:
                lines.append(f"   → {alert}")
        else:
            lines.append("   No recent alerts")

        lines.append(_SEP)
        return "\n".join(lines)

    def run_dashboard(self) -> None:
        """Demo mode: print a dashboard with simulated data."""
        print("\n🎯 Director Super Dashboard — Demo Mode\n")
        snapshot = self.update(
            cycle=1,
            market_regime="bull_trend",
            whale_flow="bullish",
            suggested_strategy_type="momentum_following",
            radar_summary={
                "opportunities_count": 7,
                "risk_level": "elevated",
                "social_sentiment": 0.42,
                "tokens_scanned": 24,
                "top_opportunities": [
                    {"symbol": "MEMEAI", "score": 82},
                    {"symbol": "DOGEX", "score": 74},
                    {"symbol": "BONK2", "score": 68},
                ],
            },
            best_strategy={
                "strategy": {"entry_indicator": "EMA", "exit_indicator": "VWAP", "period": 20},
                "sharpe": 4.2,
                "drawdown": 0.03,
                "win_rate": 0.72,
                "pnl": 120.5,
            },
            doctor_result={
                "health_score": 87.0,
                "top_recommendation": "Reduce position size slightly",
                "findings": [
                    {"severity": "info", "component": "risk_engine", "issue": "Spread within acceptable range"},
                ],
            },
            paper_state={"balance": 102_400.0, "positions": {"BTCUSDT": 1.2}},
            trade_action="BUY",
            trade_symbol="MEMEAI",
            trade_size=0.2,
            trade_price=0.0042,
            telegram_message="🟢 MEMEAI BUY signal | score=82 | whale=accumulation",
        )
        print(self.render(snapshot))


# ====================================================================
# Standalone entry point
# ====================================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Director Super Dashboard")
    parser.add_argument("--demo", action="store_true", help="Run demo mode with simulated data")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    dashboard = DirectorDashboard()
    dashboard.run_dashboard()
