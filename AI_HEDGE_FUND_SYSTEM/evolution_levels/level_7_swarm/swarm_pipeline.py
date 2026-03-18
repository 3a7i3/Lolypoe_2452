# Niveau 7 — Swarm Pipeline
from swarm_orchestrator import SwarmOrchestrator

if __name__ == "__main__":
    swarm = SwarmOrchestrator(num_meta_clusters=2)
    results = swarm.run(num_cycles=3, num_strategies=8)
    print("[Niveau 7] Swarm pipeline executed.")
    print("Final results (per meta-cluster):")
    for i, meta_results in enumerate(results):
        print(f"MetaCluster {i}: {meta_results}")
