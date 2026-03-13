from __future__ import annotations

import json
from pathlib import Path


class StrategyDatabase:
    def __init__(self, path: str = "data/best_strategies.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save_many(self, strategies: list[dict], top_n: int = 50) -> None:
        existing = self._read()
        merged = existing + strategies
        merged.sort(key=lambda x: (float(x.get("sharpe", -999.0)), -float(x.get("drawdown", 1.0))), reverse=True)
        self.path.write_text(json.dumps(merged[:top_n], indent=2), encoding="utf-8")

    def top(self, n: int = 10) -> list[dict]:
        return self._read()[:n]
