"""AI Control Center - Comprehensive monitoring dashboard."""
from __future__ import annotations

from datetime import datetime, timezone


class AIControlCenter:
    """Real-time monitoring dashboard for AI trading system."""

    def render_multi_sector_opps(self, flow_data: dict) -> str:
        opps = flow_data.get("multi_sector_opportunities", [])
        if not opps:
            return "🧩 MULTI-SECTOR OPPORTUNITIES\n  None detected\n"
        lines = ["🧩 MULTI-SECTOR OPPORTUNITIES"]
        for opp in opps[:5]:
            lines.append(
                f"  Sectors: {', '.join(opp['sectors'])} | Score: {opp['score']} | Momentum: {opp['momentum']} | Whale Flow: {opp['whale_flow']} | Volume: {opp['volume']}"
            )
        return "\n".join(lines) + "\n"
    """Real-time monitoring dashboard for AI trading system."""

    def render_header(self, cycle: int, timestamp: str) -> str:
        return (
            f"\n{'='*100}\n"
            f"🤖 AI CONTROL CENTER - CYCLE {cycle} @ {timestamp}\n"
            f"{'='*100}\n"
        )

    def render_market_regime(self, regime: dict) -> str:
        return (
            f"📊 MARKET REGIME\n"
            f"  Current: {regime.get('regime', 'unknown')}\n"
            f"  Suggested Strategy: {regime.get('strategy_type', 'neutral')}\n"
            f"  Momentum: {regime.get('momentum', 0.0):.6f}\n"
            f"  Volatility: {regime.get('realized_volatility', 0.0):.6f}\n"
            f"  Anomalies: {', '.join(regime.get('anomalies', []))}\n"
        )

    def render_whale_radar(self, whale_data: dict) -> str:
        alerts = whale_data.get("alerts", [])
        alert_str = "\n    ".join(alerts) if alerts else "None"
        sector_cov = whale_data.get("sector_coverage", {})
        if sector_cov:
            sector_lines = [f"    {sector}: {cov:.2f}%" for sector, cov in sector_cov.items()]
            sector_str = "\n".join(sector_lines)
        else:
            sector_str = "    No sector coverage data"
        return (
            f"🐋 WHALE RADAR\n"
            f"  Threat Level: {whale_data.get('threat_level', 'low').upper()}\n"
            f"  Detected Alerts:\n    {alert_str}\n"
            f"  Sector Whale Coverage:\n{sector_str}\n"
        )

    def render_strategy_performance(self, best: dict | None, stats: dict) -> str:
        if best is None:
            return "🎯 BEST STRATEGY: None found\n"

        strat = best.get("strategy", {})
        return (
            f"🎯 BEST STRATEGY\n"
            f"  Type: {strat.get('entry_indicator')} → {strat.get('exit_indicator')}\n"
            f"  Period: {strat.get('period')}, Threshold: {strat.get('threshold')}\n"
            f"  Sharpe: {best.get('sharpe', 0.0)}, Drawdown: {best.get('drawdown', 0.0)}\n"
            f"  Win Rate: {best.get('win_rate', 0.0)}, PnL: {best.get('pnl', 0.0)}\n"
            f"\n📈 SCOREBOARD STATS\n"
            f"  Total Strategies Tested: {stats.get('total_strategies', 0)}\n"
            f"  Avg Sharpe: {stats.get('avg_sharpe', 0.0)}\n"
            f"  Best Sharpe: {stats.get('best_sharpe', 0.0)}\n"
            f"  Median Sharpe: {stats.get('median_sharpe', 0.0)}\n"
        )

    def render_portfolio(self, allocation: dict, brain_info: dict) -> str:
        top_5 = sorted(allocation.items(), key=lambda x: x[1], reverse=True)[:5]
        alloc_str = "\n    ".join(f"{name}: {weight:.2%}" for name, weight in top_5)

        return (
            f"💼 PORTFOLIO ALLOCATION (Top 5)\n"
            f"    {alloc_str}\n"
            f"\n  Kelly Fraction: {brain_info.get('kelly_fraction', 0.0):.4f}\n"
            f"  Vol Target: {brain_info.get('vol_target', 0.02):.4f}\n"
            f"  Max Position: {brain_info.get('max_position', 0.3):.2%}\n"
        )

    def render_decision(self, decision: dict) -> str:
        return (
            f"⚡ EXECUTION DECISION\n"
            f"  Should Trade: {'YES' if decision.get('should_trade') else 'NO'}\n"
            f"  Reason: {decision.get('reason', 'N/A')}\n"
            f"  Risk Limits:\n"
            f"    Max Position: {decision.get('risk_limits', {}).get('max_position_size', 0.0):.4f}\n"
            f"    Stop Loss: {decision.get('risk_limits', {}).get('stop_loss_pct', 0.0):.4f}\n"
            f"    Take Profit: {decision.get('risk_limits', {}).get('take_profit_pct', 0.0):.4f}\n"
        )

    def render_system_health(self, health: dict) -> str:
        return (
            f"❤️  SYSTEM HEALTH\n"
            f"  Status: {health.get('status', 'running')}\n"
            f"  Agents Active: {health.get('agents_count', 20)}\n"
            f"  Strategies Generated: {health.get('strategies_gen', 0)}\n"
            f"  Backtests Completed: {health.get('backtests_completed', 0)}\n"
            f"  Model Version: {health.get('model_version', 1)}\n"
        )

    def render_full_report(
        self,
        cycle: int,
        market_regime: dict,
        whale_data: dict,
        best_strategy: dict | None,
        stats: dict,
        allocation: dict,
        brain_info: dict,
        decision: dict,
        health: dict,
        flow_data: dict = None,
    ) -> str:
        """Render complete control center dashboard."""
        timestamp = datetime.now(timezone.utc).isoformat()

        report = self.render_header(cycle, timestamp)
        report += self.render_market_regime(market_regime)
        report += "\n"
        report += self.render_whale_radar(whale_data)
        report += "\n"
        if flow_data:
            report += self.render_multi_sector_opps(flow_data)
            report += "\n"
        report += self.render_strategy_performance(best_strategy, stats)
        report += "\n"
        report += self.render_portfolio(allocation, brain_info)
        report += "\n"
        report += self.render_decision(decision)
        report += "\n"
        report += self.render_system_health(health)
        report += f"\n{'='*100}\n"

        return report
