# Niveau 6 — ClusterClient (simulateur de supercluster)
import random

class ClusterClient:
    def __init__(self, cluster_id):
        self.cluster_id = cluster_id

    def evaluate_strategies(self, strategies):
        # Simule l’évaluation de chaque stratégie (score aléatoire)
        return [(self.cluster_id, s, random.uniform(0, 1)) for s in strategies]
