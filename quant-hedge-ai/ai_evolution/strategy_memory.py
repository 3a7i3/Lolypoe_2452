from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MemoryConfig:
    file_path: Path = Path("databases/ai_evolution/strategy_memory.json")
    top_k_per_regime: int = 30
    max_regime_history: int = 100
    decay_per_cycle: float = 0.03
    usage_penalty_cap: float = 0.5
    usage_penalty_window: int = 20


class StrategyMemoryStore:
    """Persistent storage of top strategies by market regime."""

    def __init__(self, cfg: MemoryConfig | None = None) -> None:
        self.cfg = cfg or MemoryConfig()
        self.cfg.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load_by_regime(self, regime: str, limit: int = 20) -> list[dict]:
        payload = self._read()
        regimes = payload.get("regimes", {})
        bucket = regimes.get(regime, [])
        stability = self.get_regime_stability(regime, payload=payload)
        ranked = self._rank_for_loading(bucket, regime_stability=stability)
        selected = ranked[: max(0, limit)]

        # Track actual load frequency so heavily reused strategies get penalized later.
        if selected:
            for row in selected:
                row["usage_count"] = int(row.get("usage_count", 0)) + 1
            self._write(payload)

        return selected

    def save_for_regime(self, regime: str, strategies: list[dict]) -> int:
        payload = self._read()
        payload = self._age_all(payload)
        payload = self._record_regime_observation(payload, regime)
        regimes = payload.setdefault("regimes", {})

        existing = regimes.get(regime, [])
        merged = existing + [self._sanitize_strategy(s) for s in strategies]
        merged = self._dedupe_and_rank(merged)
        merged = merged[: self.cfg.top_k_per_regime]
        regimes[regime] = merged

        payload["last_updated_regime"] = regime
        payload["regime_count"] = len(regimes)
        self._write(payload)
        return len(merged)

    def get_regime_stability(self, regime: str, payload: dict | None = None) -> float:
        state = payload or self._read()
        history = state.get("regime_history", [])
        if not history:
            return 0.0

        window = history[-10:]
        matching = sum(1 for item in window if item == regime)
        recent_ratio = matching / len(window)

        consecutive = 0
        for item in reversed(history):
            if item != regime:
                break
            consecutive += 1

        consecutive_bonus = min(1.0, consecutive / 5.0)
        return round((recent_ratio * 0.7) + (consecutive_bonus * 0.3), 4)

    def _read(self) -> dict:
        if not self.cfg.file_path.exists():
            return {"regimes": {}, "regime_count": 0, "regime_history": []}
        try:
            return json.loads(self.cfg.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Reset corrupted memory file safely.
            return {"regimes": {}, "regime_count": 0, "regime_history": []}

    def _write(self, payload: dict) -> None:
        self.cfg.file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _sanitize_strategy(result: dict) -> dict:
        return {
            "strategy": result.get("strategy", {}),
            "sharpe": float(result.get("sharpe", 0.0)),
            "drawdown": float(result.get("drawdown", 1.0)),
            "win_rate": float(result.get("win_rate", 0.0)),
            "pnl": float(result.get("pnl", 0.0)),
            "doctor": result.get("doctor", {}),
            "age_cycles": int(result.get("age_cycles", 0)),
            "freshness": float(result.get("freshness", 1.0)),
            "usage_count": int(result.get("usage_count", 0)),
        }

    def _age_all(self, payload: dict) -> dict:
        regimes = payload.setdefault("regimes", {})
        for regime_rows in regimes.values():
            for row in regime_rows:
                age = int(row.get("age_cycles", 0)) + 1
                row["age_cycles"] = age
                row["freshness"] = max(0.1, round(1.0 - age * self.cfg.decay_per_cycle, 4))
        return payload

    def _record_regime_observation(self, payload: dict, regime: str) -> dict:
        history = payload.setdefault("regime_history", [])
        history.append(regime)
        payload["regime_history"] = history[-self.cfg.max_regime_history :]
        return payload

    @staticmethod
    def _rank_for_loading(rows: list[dict], regime_stability: float) -> list[dict]:
        def _score(row: dict) -> float:
            sharpe = float(row.get("sharpe", -999.0))
            usage_count = int(row.get("usage_count", 0))
            usage_penalty = min(0.5, usage_count / 20.0)
            stability_weight = 0.65 + regime_stability * 0.35
            return sharpe * stability_weight * (1.0 - usage_penalty)

        return sorted(
            rows,
            key=lambda x: (
                _score(x),
                float(x.get("freshness", 1.0)),
                float(x.get("win_rate", 0.0)),
                -float(x.get("drawdown", 1.0)),
                float(x.get("pnl", -999.0)),
            ),
            reverse=True,
        )

    @staticmethod
    def _dedupe_and_rank(rows: list[dict]) -> list[dict]:
        seen: dict[str, dict] = {}
        for row in rows:
            key = json.dumps(row.get("strategy", {}), sort_keys=True)
            current = seen.get(key)
            if current is None or float(row.get("sharpe", -999.0)) > float(current.get("sharpe", -999.0)):
                seen[key] = row
        return sorted(
            seen.values(),
            key=lambda x: (
                float(x.get("sharpe", -999.0)),
                float(x.get("win_rate", 0.0)),
                -float(x.get("drawdown", 1.0)),
                float(x.get("pnl", -999.0)),
            ),
            reverse=True,
        )
