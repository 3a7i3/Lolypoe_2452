# Niveau 6 — MetaOrchestrator
import random
from cluster_client import ClusterClient
from generative_ai import GenerativeAI
from network_sim import NetworkSim
import logging

logging.basicConfig(
    filename='meta_orchestrator.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class MetaOrchestrator:
    def __init__(self, num_clusters=2):
        self.clusters = [ClusterClient(cluster_id=i) for i in range(num_clusters)]
        self.generative_ai = GenerativeAI()
        self.network = NetworkSim()
        self.monitor = []

    def run(self, num_strategies=10):
        logging.info(f"Démarrage orchestration avec {len(self.clusters)} clusters et {num_strategies} stratégies.")
        # Génère des prompts et paramètres variés
        prompts = [
            "Créer une stratégie alpha",
            "Générer une stratégie momentum",
            "Concevoir une stratégie arbitrage",
            "Optimiser une stratégie multi-actifs"
        ]
        param_sets = [
            {"risk": "low", "horizon": "short", "asset": "crypto"},
            {"risk": "high", "horizon": "long", "asset": "forex"},
            {"risk": "medium", "horizon": "medium", "asset": "equity"},
            {"risk": "low", "horizon": "long", "asset": "commodities"}
        ]
        # Génère des stratégies variées
        strategies = [
            self.generative_ai.generate_strategy(
                prompt=random.choice(prompts),
                params=random.choice(param_sets)
            ) for _ in range(num_strategies)
        ]
        logging.info(f"Stratégies générées: {strategies}")
        # Compétition/collaboration : chaque cluster partage son meilleur alpha avec les autres
        results = []
        cluster_alphas = {}
        for cluster in self.clusters:
            latency, data = self.network.send(cluster.cluster_id, strategies)
            res = cluster.evaluate_strategies(data)
            # Ajoute la latence simulée à chaque résultat
            results.extend([(cluster.cluster_id, s, score, latency) for (cid, s, score) in res])
            # Enregistre le meilleur alpha de chaque cluster
            best = max(res, key=lambda x: x[2])
            cluster_alphas[cluster.cluster_id] = best
            logging.info(f"Cluster {cluster.cluster_id} latence {latency} ms, meilleur alpha: {best}")
            self.monitor.append({"cluster": cluster.cluster_id, "latency": latency, "best_alpha": best})
        # Collaboration : bonus si une stratégie est le meilleur alpha de plusieurs clusters
        alpha_counts = {}
        for cid, s, score in cluster_alphas.values():
            alpha_counts[s] = alpha_counts.get(s, 0) + 1
        # Ajoute un bonus de collaboration
        enriched_results = []
        for r in results:
            bonus = 0.1 * alpha_counts.get(r[1], 0) if alpha_counts.get(r[1], 0) > 1 else 0
            enriched_results.append((r[0], r[1], r[2] + bonus, r[3], bonus))
        # Agrège les meilleurs résultats
        enriched_results.sort(key=lambda x: x[2], reverse=True)
        logging.info(f"Top 5 résultats: {enriched_results[:5]}")
        return enriched_results[:5]  # Top 5
