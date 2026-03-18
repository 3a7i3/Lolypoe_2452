# Niveau 5 — StrategyDNA & EvolutionTree
import uuid

class StrategyDNA:
    def __init__(self, features, parents=None, score=0.0, generation=1):
        self.id = f"strat_{uuid.uuid4().hex[:6]}"
        self.parents = parents or []
        self.features = features
        self.score = score
        self.generation = generation

class EvolutionTree:
    def __init__(self):
        self.tree = {}
    def add_strategy(self, dna):
        self.tree[dna.id] = dna
    def get_lineage(self, strat_id):
        lineage = []
        current = self.tree.get(strat_id)
        while current:
            lineage.append(current.id)
            if not current.parents:
                break
            current = self.tree.get(current.parents[0])
        return lineage
