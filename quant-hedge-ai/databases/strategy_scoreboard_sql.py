"""Option N — Strategy Scoreboard persisté en SQLite.

Remplace le scoreboard JSON par une base SQLite via stdlib ``sqlite3``.
Interface identique à ``StrategyScoreboard`` (JSON) + méthode bonus
``top_by_metric()`` pour interroger par n'importe quelle métrique.

Schéma :
    strategies(
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy   TEXT NOT NULL,        -- JSON du dict stratégie
        sharpe     REAL DEFAULT 0,
        pnl        REAL DEFAULT 0,
        win_rate   REAL DEFAULT 0,
        drawdown   REAL DEFAULT 0,
        kelly      REAL DEFAULT 0,       -- fraction Kelly au moment de l'ajout
        cycle      INTEGER DEFAULT 0,
        ts         TEXT DEFAULT (datetime('now'))
    )
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS strategies (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy  TEXT    NOT NULL,
    sharpe    REAL    NOT NULL DEFAULT 0,
    pnl       REAL    NOT NULL DEFAULT 0,
    win_rate  REAL    NOT NULL DEFAULT 0,
    drawdown  REAL    NOT NULL DEFAULT 0,
    kelly     REAL    NOT NULL DEFAULT 0,
    cycle     INTEGER NOT NULL DEFAULT 0,
    ts        TEXT    NOT NULL DEFAULT (datetime('now'))
)
"""

_VALID_SORT_COLUMNS = frozenset({"sharpe", "pnl", "win_rate", "drawdown", "kelly", "cycle"})
_MAX_ENTRIES = 2_000


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convertit une valeur en float sans lever d'exception."""
    if value is None:
        return default
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


class StrategyScoreboardSQL:
    """Scoreboard SQLite — persistance totale entre les runs.

    Args:
        db_path: chemin vers le fichier ``.db``. Créé automatiquement.
        max_entries: nombre maximum de stratégies conservées.
    """

    def __init__(
        self,
        db_path: str = "databases/strategy_scoreboard.db",
        max_entries: int = _MAX_ENTRIES,
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self._init_db()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # API publique — compatible StrategyScoreboard (JSON)
    # ------------------------------------------------------------------

    def add(self, strategy: dict[str, Any], metrics: dict[str, Any]) -> None:
        """Enregistre une stratégie avec ses métriques."""
        row = (
            json.dumps(strategy, ensure_ascii=False),
            _safe_float(metrics.get("sharpe")),
            _safe_float(metrics.get("pnl")),
            _safe_float(metrics.get("win_rate")),
            _safe_float(metrics.get("drawdown")),
            _safe_float(metrics.get("kelly")),
            int(metrics.get("cycle") or 0),
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO strategies
                   (strategy, sharpe, pnl, win_rate, drawdown, kelly, cycle)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                row,
            )
            self._trim(conn)

    def top(self, n: int = 20) -> list[dict[str, Any]]:
        """Retourne les N meilleures stratégies triées par Sharpe décroissant."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM strategies ORDER BY sharpe DESC LIMIT ?", (n,)
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def top_by_metric(self, metric: str, n: int = 20) -> list[dict[str, Any]]:
        """Retourne les N meilleures stratégies triées par ``metric``.

        Args:
            metric: colonne SQL parmi sharpe, pnl, win_rate, drawdown, kelly, cycle.

        Raises:
            ValueError: si ``metric`` n'est pas une colonne valide.
        """
        if metric not in _VALID_SORT_COLUMNS:
            raise ValueError(
                f"metric={metric!r} invalide. Valeurs acceptées : {sorted(_VALID_SORT_COLUMNS)}"
            )
        order = "ASC" if metric == "drawdown" else "DESC"
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM strategies ORDER BY {metric} {order} LIMIT ?", (n,)
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def stats(self) -> dict[str, Any]:
        """Statistiques globales du scoreboard."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM strategies").fetchone()[0]
            if total == 0:
                return {
                    "total_strategies": 0,
                    "avg_sharpe": 0.0,
                    "best_sharpe": 0.0,
                    "median_sharpe": 0.0,
                }
            row = conn.execute(
                "SELECT AVG(sharpe), MAX(sharpe), MIN(sharpe) FROM strategies"
            ).fetchone()
            # Médiane via tri
            sharpes = [
                r[0]
                for r in conn.execute("SELECT sharpe FROM strategies ORDER BY sharpe").fetchall()
            ]
        median = sharpes[len(sharpes) // 2] if sharpes else 0.0
        return {
            "total_strategies": total,
            "avg_sharpe": round(row[0] or 0.0, 4),
            "best_sharpe": round(row[1] or 0.0, 4),
            "median_sharpe": round(median, 4),
        }

    def clear(self) -> None:
        """Vide la table (utile pour les tests)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM strategies")

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _trim(self, conn: sqlite3.Connection) -> None:
        """Supprime les entrées excédentaires (garde les max_entries meilleures)."""
        count = conn.execute("SELECT COUNT(*) FROM strategies").fetchone()[0]
        if count > self.max_entries:
            # Supprimer les moins bons (Sharpe le plus faible)
            excess = count - self.max_entries
            conn.execute(
                """DELETE FROM strategies WHERE id IN (
                    SELECT id FROM strategies ORDER BY sharpe ASC LIMIT ?
                )""",
                (excess,),
            )

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        try:
            d["strategy"] = json.loads(d["strategy"])
        except (json.JSONDecodeError, KeyError):
            pass
        return d
