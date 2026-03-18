import random

class StrategyEvolution:
    def mutate(self, strategy):
        mutated = strategy.copy()
        # Muter tous les seuils de toutes les conditions
        if "conditions" in mutated:
            for cond in mutated["conditions"]:
                if random.random() < 0.5:
                    cond["threshold"] *= random.uniform(0.9, 1.1)
        # Muter la taille de position
        if "position_size" in mutated and random.random() < 0.5:
            mutated["position_size"] *= random.uniform(0.9, 1.1)
        return mutated

class StrategyCrossover:
    def combine(self, strat1, strat2):
        # Combine conditions (mélange)
        conds1 = strat1.get("conditions", [])
        conds2 = strat2.get("conditions", [])
        if conds1 and conds2:
            split = random.randint(1, min(len(conds1), len(conds2)))
            child_conds = conds1[:split] + conds2[split:]
        else:
            child_conds = conds1 or conds2
        child = {
            "conditions": child_conds,
            "logic": random.choice([strat1.get("logic", "AND"), strat2.get("logic", "AND")]),
            "position_size": (strat1.get("position_size", 0.1) + strat2.get("position_size", 0.1)) / 2
        }
        return child

class EvolutionEngine:
    def __init__(self):
        self.mutator = StrategyEvolution()
        self.crossover = StrategyCrossover()

    def evolve(self, strategies):
        new_generation = []
        for _ in range(len(strategies)):
            parent1 = random.choice(strategies)
            parent2 = random.choice(strategies)
            child = self.crossover.combine(parent1, parent2)
            child = self.mutator.mutate(child)
            new_generation.append(child)
        return new_generation

class StrategyEvolutionLoop:
    def __init__(self, farm):
        self.farm = farm
        self.evolution = EvolutionEngine()

    def run(self, df, generations=5, n_strategies=200, top=20):
        strategies = self.farm.generator.generate(n_strategies)
        for g in range(generations):
            print(f"Generation {g}")
            self.farm.generator.generate = lambda n: strategies  # Patch pour injecter la population
            best = self.farm.run(df, n_strategies=n_strategies, top=top)
            strategies = self.evolution.evolve(best)
        return strategies
