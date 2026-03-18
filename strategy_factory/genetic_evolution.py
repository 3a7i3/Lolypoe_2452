import random
from strategy_factory.reproduction import ReproductionEngine

class GeneticEvolution:
    def __init__(self):
        self.reproduction = ReproductionEngine()

    def evolve(self, genomes, scores):
        ranked = list(zip(genomes, scores))
        ranked.sort(key=lambda x: x[1], reverse=True)
        survivors = [g for g,_ in ranked[:20]]
        children = []
        for _ in range(len(survivors)):
            p1 = random.choice(survivors)
            p2 = random.choice(survivors)
            child = self.reproduction.crossover(p1,p2)
            child.mutate()
            children.append(child)
        return survivors + children
