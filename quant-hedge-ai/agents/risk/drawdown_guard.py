from __future__ import annotations


class DrawdownGuard:
    def adjust_position_size(self, drawdown: float, base_size: float = 1.0) -> float:
        if drawdown <= 0:
            return base_size
        factor = max(0.1, 1.0 - drawdown * 2.5)
        return round(base_size * factor, 4)
