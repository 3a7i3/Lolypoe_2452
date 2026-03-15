"""
Gère l'évolution des stratégies par mutation, crossover, sélection naturelle.
"""

class StrategyEvolution:
    def __init__(self):
        self.population = []

    def dna_mutation(self, strategy):
        # Simule une mutation simple (ex: modifie un paramètre)
        mutated = dict(strategy)
        mutated['mutated'] = True
        return mutated

    def dna_crossover(self, strat1, strat2):
        # Simule un crossover (mélange de paramètres)
        child = {**strat1, **strat2}
        child['crossover'] = True
        return child

    def population_manager(self, population):
        # Sélectionne les meilleurs (par PnL)
        return sorted(population, key=lambda s: s.get('pnl', 0), reverse=True)[:2]

    def evolution_cycle(self, population):
        # Applique mutation et crossover sur la population
        if len(population) < 2:
            return population
        best = self.population_manager(population)
        child = self.dna_crossover(best[0], best[1])
        mutated = self.dna_mutation(child)
        return best + [mutated]

# Test minimal du module
if __name__ == '__main__':
    evol = StrategyEvolution()
    pop = [
        {'strategy': 'A', 'pnl': 1.2},
        {'strategy': 'B', 'pnl': -0.5},
        {'strategy': 'C', 'pnl': 0.7}
    ]
    print('Best:', evol.population_manager(pop))
    print('Evolved:', evol.evolution_cycle(pop))
