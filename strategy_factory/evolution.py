from strategy_factory.genetic_evolution import GeneticEvolution

class EvolutionEngine:
    def __init__(self):
        self.genetic = GeneticEvolution()

    def evolve(self, genomes, scores):
        return self.genetic.evolve(genomes, scores)
