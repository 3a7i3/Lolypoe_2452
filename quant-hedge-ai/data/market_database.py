from __future__ import annotations

import json
from pathlib import Path


class MarketDatabase:
    def __init__(self, path: str = "data/market_snapshots.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, snapshot: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(snapshot) + "\n")
