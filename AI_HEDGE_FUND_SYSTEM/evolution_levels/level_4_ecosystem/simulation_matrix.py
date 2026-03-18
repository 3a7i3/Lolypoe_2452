# Simulation Matrix — Niveau 4
import random
class SimulationMatrix:
    def simulate(self, strategy):
        # Simule slippage, latency, fees, liquidity
        pnl = random.uniform(-0.05, 0.1)
        return {"id": strategy["id"], "pnl": pnl}
