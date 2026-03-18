from strategy_factory.genome import StrategyGenome
from strategy_factory.generator import StrategyGenerator
from strategy_factory.genetic_evolution import GeneticEvolution
import random

def test_genetic_evolution_cycle():
    generator = StrategyGenerator()
    evolution = GeneticEvolution()
    # Generate initial population
    genomes = generator.generate(n=50)
    # Fake scores for testing (randomized)
    scores = [random.uniform(-1, 1) for _ in genomes]
    # Evolve
    next_gen = evolution.evolve(genomes, scores)
    assert len(next_gen) == 40  # 20 survivors + 20 children
    print("Genetic evolution cycle test passed.")

if __name__ == "__main__":
    test_genetic_evolution_cycle()
