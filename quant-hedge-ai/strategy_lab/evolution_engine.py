# evolution_engine.py
"""
Moteur d'évolution de stratégies (mutation, crossover, génération).
"""
import random

class StrategyEvolutionEngine:
    def __init__(self, mutation_rate=0.1):
        self.mutation_rate = mutation_rate

    def mutate(self, strategy):
        new_strategy = strategy.copy()
        if random.random() < self.mutation_rate:
            if "threshold" in new_strategy:
                new_strategy["threshold"] *= random.uniform(0.9, 1.1)
        if random.random() < self.mutation_rate:
            if "window" in new_strategy:
                new_strategy["window"] += random.choice([-1, 1])
        return new_strategy

    def crossover(self, strategy_a, strategy_b):
        child = {}
        for key in strategy_a.keys():
            if random.random() > 0.5:
                child[key] = strategy_a[key]
            else:
                child[key] = strategy_b.get(key, strategy_a[key])
        return child

    def evolve(self, best_strategies, population_size):
        new_population = []
        while len(new_population) < population_size:
            parent_a = random.choice(best_strategies)
            parent_b = random.choice(best_strategies)
            child = self.crossover(parent_a, parent_b)
            child = self.mutate(child)
            new_population.append(child)
        return new_population
