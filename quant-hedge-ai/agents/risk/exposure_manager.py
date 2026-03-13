from __future__ import annotations


class ExposureManager:
    def cap(self, proposed: dict[str, float], max_per_symbol: float = 0.25) -> dict[str, float]:
        capped = {k: min(max_per_symbol, float(v)) for k, v in proposed.items()}
        total = sum(capped.values()) or 1.0
        return {k: round(v / total, 4) for k, v in capped.items()}
