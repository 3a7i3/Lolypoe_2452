"""
Option AE — SystemState thread-safe partagé entre la boucle V9.1 et l'API REST.

La boucle principale écrit dans cet état à chaque cycle.
L'API FastAPI lit depuis cet état sans bloquer la boucle.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SystemState:
    """Snapshot de l'état courant du système, mise à jour à chaque cycle."""

    # Contrôle de la boucle
    paused: bool = False
    running: bool = True

    # Cycle courant
    cycle: int = 0
    max_cycles: int = 0

    # Marché
    regime: str = "unknown"
    symbol: str = "BTCUSDT"
    data_source: str = "synthetic"

    # Paper trading
    equity: float = 0.0
    pnl: float = 0.0
    return_pct: float = 0.0
    drawdown_pct: float = 0.0
    win_rate: float = 0.0
    trades_count: int = 0

    # Stratégie
    best_strategy_type: str = ""
    best_sharpe: float = 0.0

    # Circuit breaker
    circuit_breaker_ok: bool = True
    circuit_breaker_reason: str = ""

    # Config runtime (snapshot JSON-serializable)
    config_snapshot: dict[str, Any] = field(default_factory=dict)

    # Scoreboard top-5
    scoreboard_top: list[dict[str, Any]] = field(default_factory=list)

    # Timestamp dernière mise à jour
    last_updated: str = ""

    # Lock interne (non sérialisé)
    _lock: threading.Lock = field(default_factory=threading.Lock, compare=False, repr=False)

    def update(self, **kwargs: Any) -> None:
        """Met à jour les champs de l'état de manière thread-safe."""
        with self._lock:
            for k, v in kwargs.items():
                if hasattr(self, k) and not k.startswith("_"):
                    object.__setattr__(self, k, v)

    def snapshot(self) -> dict[str, Any]:
        """Retourne un dict thread-safe de l'état courant."""
        with self._lock:
            return {
                "paused": self.paused,
                "running": self.running,
                "cycle": self.cycle,
                "max_cycles": self.max_cycles,
                "regime": self.regime,
                "symbol": self.symbol,
                "data_source": self.data_source,
                "equity": self.equity,
                "pnl": self.pnl,
                "return_pct": self.return_pct,
                "drawdown_pct": self.drawdown_pct,
                "win_rate": self.win_rate,
                "trades_count": self.trades_count,
                "best_strategy_type": self.best_strategy_type,
                "best_sharpe": self.best_sharpe,
                "circuit_breaker_ok": self.circuit_breaker_ok,
                "circuit_breaker_reason": self.circuit_breaker_reason,
                "last_updated": self.last_updated,
            }

    def pause(self) -> None:
        with self._lock:
            object.__setattr__(self, "paused", True)

    def resume(self) -> None:
        with self._lock:
            object.__setattr__(self, "paused", False)

    def is_paused(self) -> bool:
        with self._lock:
            return self.paused


# Instance globale — importée par main_v91.py et rest_api.py
_state = SystemState()


def get_state() -> SystemState:
    return _state
