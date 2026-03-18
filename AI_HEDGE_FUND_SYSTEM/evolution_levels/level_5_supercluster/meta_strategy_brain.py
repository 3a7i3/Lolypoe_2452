# Niveau 5 — MetaStrategyBrain

class MetaStrategyBrain:
    def select(self, strategies):
        # Trie les stratégies par score décroissant
        ranked = sorted(
            strategies,
            key=lambda s: s["score"],
            reverse=True
        )
        # Retourne les 5 meilleures
        return ranked[:5]
