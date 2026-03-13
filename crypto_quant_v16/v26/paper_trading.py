"""Paper trading journal for V26 dashboard.

Manages in-memory positions with JSON persistence to data/paper_trades.json.
No network calls — all executions happen at the price provided by the caller.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

_JOURNAL_PATH = Path(__file__).parent.parent / "data" / "paper_trades.json"


class PaperTrader:
    """Lightweight paper trading engine.

    Usage:
        trader = PaperTrader(capital=10_000.0)
        pid = trader.open_position("BTC/USDT", "BUY", entry=84000, size_usd=500, sl=82320, tp=87360)
        trader.update_unrealized({"BTC/USDT": 85000})
        trader.close_position(pid, exit_price=85000)
    """

    def __init__(self, capital: float = 10_000.0) -> None:
        self.initial_capital = capital
        self.cash = capital
        self.positions: Dict[str, dict] = {}   # position_id → position dict
        self.closed_trades: List[dict] = []
        self._load()

    # ── persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if _JOURNAL_PATH.exists():
            try:
                data = json.loads(_JOURNAL_PATH.read_text(encoding="utf-8"))
                self.cash = float(data.get("cash", self.initial_capital))
                self.positions = data.get("positions", {})
                self.closed_trades = data.get("closed_trades", [])
            except Exception:
                pass  # corrupt file → start fresh

    def _save(self) -> None:
        _JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        _JOURNAL_PATH.write_text(
            json.dumps(
                {
                    "cash": self.cash,
                    "positions": self.positions,
                    "closed_trades": self.closed_trades,
                },
                default=str,
                indent=2,
            ),
            encoding="utf-8",
        )

    # ── trading operations ────────────────────────────────────────────────────

    def open_position(
        self,
        symbol: str,
        side: str,          # "BUY" or "SELL"
        entry_price: float,
        size_usd: float,
        sl_price: float,
        tp_price: float,
    ) -> Optional[str]:
        """Open a paper position.  Returns position_id, or None if insufficient cash."""
        size_usd = min(size_usd, self.cash)
        if size_usd < 1.0:
            return None
        pid = str(uuid.uuid4())[:8]
        qty = size_usd / entry_price
        self.positions[pid] = {
            "id": pid,
            "symbol": symbol,
            "side": side,
            "entry_price": round(entry_price, 4),
            "qty": round(qty, 8),
            "size_usd": round(size_usd, 2),
            "sl": round(sl_price, 4),
            "tp": round(tp_price, 4),
            "open_time": datetime.utcnow().isoformat(),
            "unrealized_pnl": 0.0,
            "unrealized_pct": 0.0,
        }
        self.cash -= size_usd
        self._save()
        return pid

    def close_position(self, position_id: str, exit_price: float) -> Optional[dict]:
        """Close a position at exit_price and record the realized PnL."""
        pos = self.positions.pop(position_id, None)
        if pos is None:
            return None
        if pos["side"] == "BUY":
            pnl = (exit_price - pos["entry_price"]) * pos["qty"]
        else:
            pnl = (pos["entry_price"] - exit_price) * pos["qty"]
        pct = pnl / pos["size_usd"] if pos["size_usd"] else 0.0
        trade = {
            **pos,
            "exit_price": round(exit_price, 4),
            "pnl": round(pnl, 2),
            "pct": round(pct, 4),
            "close_time": datetime.utcnow().isoformat(),
        }
        self.closed_trades.append(trade)
        self.cash += pos["size_usd"] + pnl
        self._save()
        return trade

    def close_all(self, current_prices: Dict[str, float]) -> List[dict]:
        """Close all open positions at current prices.  Returns list of closed trade dicts."""
        closed = []
        for pid in list(self.positions):
            sym = self.positions[pid]["symbol"]
            price = current_prices.get(sym)
            if price is not None:
                t = self.close_position(pid, price)
                if t:
                    closed.append(t)
        return closed

    def update_unrealized(self, current_prices: Dict[str, float]) -> None:
        """Recalculate unrealized PnL for all open positions."""
        for pos in self.positions.values():
            price = current_prices.get(pos["symbol"])
            if price is None:
                continue
            if pos["side"] == "BUY":
                pnl = (price - pos["entry_price"]) * pos["qty"]
            else:
                pnl = (pos["entry_price"] - price) * pos["qty"]
            pos["unrealized_pnl"] = round(pnl, 2)
            pos["unrealized_pct"] = round(pnl / pos["size_usd"], 4) if pos["size_usd"] else 0.0
        self._save()

    def reset(self) -> None:
        """Wipe all positions, trade history, and restore initial capital."""
        self.cash = self.initial_capital
        self.positions = {}
        self.closed_trades = []
        self._save()

    # ── summary helpers ───────────────────────────────────────────────────────

    def get_positions_df(self) -> pd.DataFrame:
        if not self.positions:
            return pd.DataFrame(
                columns=["id", "symbol", "side", "entry_price", "qty", "size_usd",
                         "sl", "tp", "unrealized_pnl", "unrealized_pct", "open_time"]
            )
        return pd.DataFrame(list(self.positions.values()))

    def get_trades_df(self) -> pd.DataFrame:
        if not self.closed_trades:
            return pd.DataFrame(
                columns=["id", "symbol", "side", "entry_price", "exit_price",
                         "qty", "pnl", "pct", "close_time"]
            )
        return pd.DataFrame(self.closed_trades)

    @property
    def total_pnl(self) -> float:
        return sum(t["pnl"] for t in self.closed_trades)

    @property
    def equity(self) -> float:
        unrealized = sum(p["unrealized_pnl"] for p in self.positions.values())
        locked = sum(p["size_usd"] for p in self.positions.values())
        return self.cash + locked + unrealized

    @property
    def win_rate(self) -> float:
        if not self.closed_trades:
            return 0.0
        return sum(1 for t in self.closed_trades if t["pnl"] > 0) / len(self.closed_trades)
