# Strategy Designer — Niveau 4
class StrategyDesigner:
    def design(self, features, n=5):
        return [
            {"id": f"S{i}", "rule": f"ma > {1+i*0.1} and vol < {2+i*0.2}"} for i in range(n)
        ]
