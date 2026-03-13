from __future__ import annotations

from datetime import datetime, timezone


class SystemMonitor:
    def heartbeat(self, cycle: int) -> dict:
        return {
            "cycle": cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "running",
        }
