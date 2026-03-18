# Niveau 6 — Meta-Cluster Pipeline
from meta_orchestrator import MetaOrchestrator

if __name__ == "__main__":
    orchestrator = MetaOrchestrator(num_clusters=2)
    top_results = orchestrator.run(num_strategies=10)
    print("[Niveau 6] Meta-Cluster pipeline executed.")
    print("Top 5 results (cluster, strategy, score, latency ms, collaboration bonus):")
    for r in top_results:
        print(r)
