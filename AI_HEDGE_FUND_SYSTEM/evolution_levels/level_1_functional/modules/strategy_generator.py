# Strategy Generator — Niveau 1
class StrategyGenerator:
    def generate(self, features, n=5):
        # Génère n stratégies simples
        return [
            {"id": f"S{i}", "rule": f"ma > {1+i*0.1}"} for i in range(n)
        ]
