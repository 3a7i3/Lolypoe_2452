# Niveau 7 — SwarmOrchestrator
from swarm_intelligence import SwarmIntelligence
import importlib

class SwarmOrchestrator:
    def __init__(self, num_meta_clusters=2):
        # Import dynamique du MetaOrchestrator niveau 6
        meta_mod = importlib.import_module('AI_HEDGE_FUND_SYSTEM.evolution_levels.level_6_metacluster.meta_orchestrator')
        self.meta_clusters = [meta_mod.MetaOrchestrator(num_clusters=2) for _ in range(num_meta_clusters)]
        self.swarm_ai = SwarmIntelligence()

    def run(self, num_cycles=3, num_strategies=10):
        for cycle in range(num_cycles):
            print(f"[Swarm] Cycle {cycle+1}")
            for mc in self.meta_clusters:
                mc.last_results = mc.run(num_strategies=num_strategies)
            migrated = self.swarm_ai.migrate_strategies(self.meta_clusters)
            self.swarm_ai.adapt(self.meta_clusters)
            print(f"[Swarm] Migration: {migrated}")
        # Monitoring final
        return [mc.last_results for mc in self.meta_clusters]
