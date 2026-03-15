import random

class StrategyEvolutionEngine:
    def __init__(self):
        self.population = []

    def generate_initial_population(self, N):
        self.population = [{"name": f"strat_{i}", "params": self.random_params(), "score": 0} for i in range(N)]

    def random_params(self):
        return {"window": random.randint(5, 50), "threshold": random.random()}

    def evolve(self):
        self.population.sort(key=lambda x: x['score'], reverse=True)
        top = self.population[:len(self.population)//2]
        new_population = top.copy()
        for s in top:
            mutated = s.copy()
            mutated['params'] = self.mutate(s['params'])
            new_population.append(mutated)
        self.population = new_population

    def mutate(self, params):
        params['window'] = max(1, params['window'] + random.randint(-2,2))
        params['threshold'] = min(1.0, max(0.0, params['threshold'] + random.uniform(-0.05, 0.05)))
        return params
