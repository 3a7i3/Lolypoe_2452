import random

class SimulatedExecutionEngine:
    def __init__(self):
        self.history = []

    def execute_trades(self, allocation):
        # Simule l'exécution et le slippage
        results = {}
        for strat, weight in allocation.items():
            # Simule un PnL aléatoire autour de 0
            pnl = round(random.uniform(-0.05, 0.08) * weight, 4)
            results[strat] = pnl
        self.history.append(results)
        return results

    def get_performance(self):
        # Retourne la somme des PnL de la dernière exécution
        if not self.history:
            return {"profit": 0.0}
        last = self.history[-1]
        return {"profit": sum(last.values())}
