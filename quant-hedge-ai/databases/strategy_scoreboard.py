"""Strategy Scoreboard - Persistent storage and ranking of strategies."""
from __future__ import annotations

import json
from pathlib import Path


class StrategyScoreboard:
    """Maintains a leaderboard of all tested strategies."""

    def __init__(self, path: str = "databases/strategy_scoreboard.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            return []

    def add(self, strategy: dict, metrics: dict) -> None:
        """Add strategy + metrics to scoreboard."""
        scoreboard = self._read()
        entry = {
            "strategy": strategy,
            "metrics": metrics,
            "timestamp": metrics.get("cycle", 0),
        }
        scoreboard.append(entry)
        scoreboard.sort(key=lambda x: float(x["metrics"].get("sharpe", -999.0)), reverse=True)
        self.path.write_text(json.dumps(scoreboard[-500:], indent=2), encoding="utf-8")

    def top(self, n: int = 20) -> list[dict]:
        """Get top N strategies."""
        return self._read()[:n]

    def stats(self) -> dict:
        """Get scoreboard statistics."""
        board = self._read()
        if not board:
            return {"total_strategies": 0, "avg_sharpe": 0.0, "best_sharpe": 0.0}

        sharpes = [float(b["metrics"].get("sharpe", 0.0)) for b in board]
        return {
            "total_strategies": len(board),
            "avg_sharpe": round(sum(sharpes) / len(sharpes), 4) if sharpes else 0.0,
            "best_sharpe": round(max(sharpes), 4) if sharpes else 0.0,
            "median_sharpe": round(sorted(sharpes)[len(sharpes) // 2], 4) if sharpes else 0.0,
        }
