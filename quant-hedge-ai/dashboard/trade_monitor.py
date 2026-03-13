"""Trade Monitor — tracks active positions, executed trades and P&L."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """A single executed or paper trade."""

    symbol: str
    action: str  # "BUY" | "SELL" | "HOLD"
    size: float
    price: float
    cycle: int
    timestamp: str = ""
    pnl: float = 0.0
    status: str = "open"  # "open" | "closed" | "blocked"
    source: str = "paper"  # "paper" | "live" | "radar"


@dataclass
class TradeMonitorReport:
    """Trade monitoring summary for one cycle."""

    recent_trades: list[TradeRecord] = field(default_factory=list)
    active_positions: dict[str, float] = field(default_factory=dict)
    total_pnl: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    blocked_count: int = 0
    balance: float = 0.0
    cycle: int = 0

    @property
    def win_rate(self) -> float:
        total = self.win_count + self.loss_count
        return self.win_count / total if total > 0 else 0.0


class TradeMonitor:
    """Tracks all paper trades, positions and P&L across cycles."""

    def __init__(self, starting_balance: float = 100_000.0) -> None:
        self._trades: list[TradeRecord] = []
        self._balance = starting_balance
        self._starting_balance = starting_balance

    def record_trade(
        self,
        symbol: str,
        action: str,
        size: float,
        price: float,
        cycle: int,
        pnl: float = 0.0,
        status: str = "open",
        source: str = "paper",
    ) -> TradeRecord:
        """Record a trade execution."""
        trade = TradeRecord(
            symbol=symbol,
            action=action,
            size=size,
            price=price,
            cycle=cycle,
            timestamp=datetime.now(timezone.utc).isoformat(),
            pnl=pnl,
            status=status,
            source=source,
        )
        self._trades.append(trade)
        if pnl != 0:
            self._balance += pnl
        logger.debug("TradeMonitor: recorded %s %s @ %.4f (pnl=%.2f)", action, symbol, price, pnl)
        return trade

    def record_paper_state(self, paper_state: dict, cycle: int) -> None:
        """Import paper trading engine state dict (from PaperTradingEngine.execute())."""
        balance = paper_state.get("balance", self._balance)
        self._balance = float(balance)

    def tick(self, cycle: int, paper_state: dict | None = None) -> TradeMonitorReport:
        """Generate a trade monitor report for this cycle."""
        if paper_state:
            self.record_paper_state(paper_state, cycle)

        recent = [t for t in self._trades if t.cycle >= max(1, cycle - 5)]
        positions: dict[str, float] = {}
        for t in recent:
            if t.action == "BUY":
                positions[t.symbol] = positions.get(t.symbol, 0.0) + t.size
            elif t.action == "SELL":
                positions[t.symbol] = positions.get(t.symbol, 0.0) - t.size
        positions = {k: v for k, v in positions.items() if abs(v) > 0.001}

        closed = [t for t in self._trades if t.pnl != 0]
        wins = sum(1 for t in closed if t.pnl > 0)
        losses = sum(1 for t in closed if t.pnl < 0)
        blocked = sum(1 for t in self._trades if t.status == "blocked")

        return TradeMonitorReport(
            recent_trades=recent[-10:],
            active_positions=positions,
            total_pnl=self._balance - self._starting_balance,
            win_count=wins,
            loss_count=losses,
            blocked_count=blocked,
            balance=self._balance,
            cycle=cycle,
        )

    def render(self, report: TradeMonitorReport) -> str:
        """Render trade monitor as formatted text."""
        pnl_sign = "+" if report.total_pnl >= 0 else ""
        lines = [
            "💰 TRADE MONITOR",
            f"   Balance : ${report.balance:,.2f}  |  P&L: {pnl_sign}{report.total_pnl:,.2f}",
            f"   Win Rate: {report.win_rate:.1%}  (W:{report.win_count} L:{report.loss_count} Blocked:{report.blocked_count})",
        ]
        if report.active_positions:
            lines.append("   Active Positions:")
            for sym, qty in report.active_positions.items():
                lines.append(f"      {sym:<16s}  qty={qty:.4f}")
        else:
            lines.append("   Active Positions: None")

        if report.recent_trades:
            lines.append(f"   Recent Trades (last 5 cycles):")
            for t in report.recent_trades[-5:]:
                pnl_str = f"  pnl={t.pnl:+.2f}" if t.pnl != 0 else ""
                lines.append(f"      [{t.action:4s}] {t.symbol:<16s} size={t.size:.4f} @ {t.price:.4f}{pnl_str}")
        return "\n".join(lines)
