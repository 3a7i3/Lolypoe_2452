# Niveau 7 — Swarm Intelligence Engine
import random

class SwarmIntelligence:
    def __init__(self):
        self.history = []

    def migrate_strategies(self, meta_clusters):
        # Sélectionne les meilleures stratégies de chaque meta-cluster
        all_strats = []
        for mc in meta_clusters:
            all_strats.extend(mc.last_results)
        # Prend les top stratégies et les redistribue
        top = sorted(all_strats, key=lambda x: x[2], reverse=True)[:len(meta_clusters)]
        for i, mc in enumerate(meta_clusters):
            mc.inject_strategy(top[i][1])
        self.history.append(top)
        return top

    def adapt(self, meta_clusters):
        # Simule une adaptation globale (ex: modifie un paramètre global)
        for mc in meta_clusters:
            mc.adaptation_level = random.uniform(0, 1)
