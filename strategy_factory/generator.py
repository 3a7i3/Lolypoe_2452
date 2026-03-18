from strategy_factory.genome import StrategyGenome

class StrategyGenerator:
    def generate(self, n=200):
        genomes = []
        for _ in range(n):
            genomes.append(StrategyGenome())
        return genomes
