"""Option O — LivePaperEngine : moteur de paper trading avec PnL temps réel.

Remplace le PaperTradingEngine basique par un moteur complet :
- Positions avec coût moyen (avg cost)
- PnL réalisé par trade (FIFO simplifié)
- PnL non-réalisé depuis les prix courants
- Equity curve (snapshot par execute())
- Drawdown depuis le pic d'equity
- Win rate sur les trades fermés
- Historique complet des trades
- summary() dict pour le dashboard

Interface rétrocompatible : execute(order, mark_price) → dict.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TradeRecord:
    """Enregistrement d'un trade individuel."""

    cycle: int
    symbol: str
    action: str          # BUY | SELL
    size: float
    price: float
    cost: float          # notionnel en USD
    realized_pnl: float  # 0 pour un BUY, PnL réalisé pour un SELL
    balance_after: float


class LivePaperEngine:
    """Moteur de paper trading avec PnL temps réel.

    Args:
        initial_balance: capital initial en USD.
    """

    def __init__(self, initial_balance: float = 100_000.0) -> None:
        if initial_balance <= 0:
            raise ValueError(f"initial_balance doit être > 0, reçu: {initial_balance}")

        self.initial_balance: float = initial_balance
        self.balance: float = initial_balance

        # Positions : symbol → quantité détenue
        self.positions: dict[str, float] = {}
        # Coût moyen d'entrée : symbol → prix moyen d'achat
        self.avg_cost: dict[str, float] = {}
        # Derniers prix observés (pour unrealized PnL)
        self.last_prices: dict[str, float] = {}

        # Métriques
        self.realized_pnl: float = 0.0
        self.peak_equity: float = initial_balance
        self.trade_log: list[TradeRecord] = []
        self.equity_curve: list[float] = [initial_balance]
        self._last_trade_pnl: float = 0.0  # PnL du dernier trade (option P)

        self._cycle: int = 0

    # ------------------------------------------------------------------
    # Interface principale (rétrocompatible)
    # ------------------------------------------------------------------

    def execute(self, order: dict[str, Any], mark_price: float, cycle: int = 0) -> dict[str, Any]:
        """Exécute un ordre paper et retourne l'état complet.

        Args:
            order: dict avec keys ``symbol``, ``action``, ``size``.
            mark_price: prix de marché courant pour le symbole.
            cycle: numéro de cycle (pour le trade log).

        Returns:
            dict avec balance, positions, equity, pnl, drawdown, win_rate, etc.
        """
        symbol = order["symbol"]
        action = str(order.get("action", "HOLD")).upper()
        size = max(0.0, float(order.get("size", 0.0)))

        self._cycle = cycle
        self.last_prices[symbol] = mark_price
        realized_pnl_trade = 0.0
        self._last_trade_pnl = 0.0

        if action == "BUY" and size > 0:
            notional = size * mark_price
            if self.balance >= notional:
                # Mise à jour du coût moyen (average cost)
                current_qty = self.positions.get(symbol, 0.0)
                current_avg = self.avg_cost.get(symbol, mark_price)
                new_qty = current_qty + size
                self.avg_cost[symbol] = (current_qty * current_avg + size * mark_price) / new_qty
                self.positions[symbol] = new_qty
                self.balance -= notional
                self._record(cycle, symbol, "BUY", size, mark_price, notional, 0.0)

        elif action == "SELL" and size > 0:
            current_qty = self.positions.get(symbol, 0.0)
            sold_qty = min(current_qty, size)
            if sold_qty > 0:
                avg = self.avg_cost.get(symbol, mark_price)
                realized_pnl_trade = (mark_price - avg) * sold_qty
                self.realized_pnl += realized_pnl_trade
                self._last_trade_pnl = realized_pnl_trade
                self.balance += sold_qty * mark_price
                remaining = current_qty - sold_qty
                self.positions[symbol] = remaining
                if remaining < 1e-10:
                    self.positions.pop(symbol, None)
                    self.avg_cost.pop(symbol, None)
                notional = sold_qty * mark_price
                self._record(cycle, symbol, "SELL", sold_qty, mark_price, notional, realized_pnl_trade)

        # Snapshot equity + drawdown
        current_equity = self._equity()
        self.equity_curve.append(current_equity)
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        return self._state()

    # ------------------------------------------------------------------
    # Métriques dérivées
    # ------------------------------------------------------------------

    def equity(self) -> float:
        """Equity courante = cash + valeur mark-to-market des positions."""
        return self._equity()

    def unrealized_pnl(self) -> float:
        """PnL non-réalisé = somme (prix courant - avg_cost) * qty."""
        total = 0.0
        for sym, qty in self.positions.items():
            if qty > 0:
                price = self.last_prices.get(sym, self.avg_cost.get(sym, 0.0))
                cost = self.avg_cost.get(sym, price)
                total += (price - cost) * qty
        return total

    def total_return_pct(self) -> float:
        """Rendement total en % depuis le capital initial."""
        return (self._equity() - self.initial_balance) / self.initial_balance * 100.0

    def drawdown_pct(self) -> float:
        """Drawdown courant depuis le pic d'equity en %."""
        eq = self._equity()
        if self.peak_equity <= 0:
            return 0.0
        return max(0.0, (self.peak_equity - eq) / self.peak_equity * 100.0)

    def max_drawdown_pct(self) -> float:
        """Drawdown maximum observé sur toute la durée."""
        if len(self.equity_curve) < 2:
            return 0.0
        peak = self.equity_curve[0]
        max_dd = 0.0
        for eq in self.equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100.0 if peak > 0 else 0.0
            max_dd = max(max_dd, dd)
        return round(max_dd, 4)

    def win_rate(self) -> float:
        """Win rate sur les trades de type SELL avec PnL calculé."""
        sells = [t for t in self.trade_log if t.action == "SELL"]
        if not sells:
            return 0.0
        wins = sum(1 for t in sells if t.realized_pnl > 0)
        return wins / len(sells)

    def summary(self) -> dict[str, Any]:
        """Dict complet pour le dashboard."""
        sells = [t for t in self.trade_log if t.action == "SELL"]
        return {
            "balance": round(self.balance, 2),
            "positions": {k: round(v, 6) for k, v in self.positions.items() if v > 0},
            "equity": round(self._equity(), 2),
            "initial_balance": self.initial_balance,
            "realized_pnl": round(self.realized_pnl, 4),
            "unrealized_pnl": round(self.unrealized_pnl(), 4),
            "total_return_pct": round(self.total_return_pct(), 4),
            "drawdown_pct": round(self.drawdown_pct(), 4),
            "max_drawdown_pct": round(self.max_drawdown_pct(), 4),
            "peak_equity": round(self.peak_equity, 2),
            "win_rate": round(self.win_rate(), 4),
            "trade_count": len(self.trade_log),
            "sell_count": len(sells),
            "equity_curve_len": len(self.equity_curve),
        }

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _equity(self) -> float:
        total = self.balance
        for sym, qty in self.positions.items():
            price = self.last_prices.get(sym, self.avg_cost.get(sym, 0.0))
            total += qty * price
        return total

    def _record(
        self,
        cycle: int,
        symbol: str,
        action: str,
        size: float,
        price: float,
        cost: float,
        realized_pnl: float,
    ) -> None:
        self.trade_log.append(
            TradeRecord(
                cycle=cycle,
                symbol=symbol,
                action=action,
                size=round(size, 6),
                price=round(price, 6),
                cost=round(cost, 4),
                realized_pnl=round(realized_pnl, 4),
                balance_after=round(self.balance, 2),
            )
        )

    def _state(self) -> dict[str, Any]:
        """Dict de retour de execute() — rétrocompatible + métriques étendues."""
        return {
            "balance": round(self.balance, 2),
            "positions": {k: round(v, 6) for k, v in self.positions.items() if v > 0},
            "equity": round(self._equity(), 2),
            "realized_pnl": round(self.realized_pnl, 4),
            "unrealized_pnl": round(self.unrealized_pnl(), 4),
            "total_return_pct": round(self.total_return_pct(), 4),
            "drawdown_pct": round(self.drawdown_pct(), 4),
            "win_rate": round(self.win_rate(), 4),
            "trade_count": len(self.trade_log),
            "last_trade_pnl": round(self._last_trade_pnl, 4),
        }
