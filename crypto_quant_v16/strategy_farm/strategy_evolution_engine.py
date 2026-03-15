import random
from typing import List, Dict, Any
from copy import deepcopy

class StrategyEvolutionEngine:
    """
    Module d'évolution des stratégies :
    - Sélection des plus robustes
    - Croisement (crossover)
    - Mutation pour exploration
    """

    def __init__(self, population: List[Dict[str, Any]]):
        self.population = population

    # -------------------------
    # Sélection : top X % selon un score fictif
    # -------------------------
    def selection(self, fitness_scores: List[float], top_percent: float = 0.3) -> List[Dict[str, Any]]:
        """
        Sélectionne les stratégies les plus performantes
        """
        paired = list(zip(self.population, fitness_scores))
        paired.sort(key=lambda x: x[1], reverse=True)
        cutoff = max(1, int(len(paired) * top_percent))
        selected = [p[0] for p in paired[:cutoff]]
        return selected

    # -------------------------
    # Croisement : mélanger les paramètres
    # -------------------------
    def crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        child = {}
        for key in parent1:
            child[key] = random.choice([parent1[key], parent2.get(key, parent1[key])])
        return child

    # -------------------------
    # Mutation : léger changement aléatoire
    # -------------------------
    def mutate(self, strategy: Dict[str, Any], mutation_rate: float = 0.1) -> Dict[str, Any]:
        new_strategy = deepcopy(strategy)
        for key, value in strategy.items():
            if isinstance(value, (int, float)) and random.random() < mutation_rate:
                if isinstance(value, int):
                    new_strategy[key] = max(1, value + random.randint(-2, 2))
                else:
                    new_strategy[key] = round(value * (1 + random.uniform(-0.2, 0.2)), 3)
        return new_strategy

    # -------------------------
    # Génération nouvelle population
    # -------------------------
    def evolve_population(self, fitness_scores: List[float], top_percent: float = 0.3, mutation_rate: float = 0.1) -> List[Dict[str, Any]]:
        selected = self.selection(fitness_scores, top_percent)
        new_population = []

        while len(new_population) < len(self.population):
            if len(selected) == 1:
                parent1 = parent2 = selected[0]
            else:
                parent1, parent2 = random.sample(selected, 2)
            child = self.crossover(parent1, parent2)
            child = self.mutate(child, mutation_rate)
            new_population.append(child)

        self.population = new_population
        return self.population

if __name__ == "__main__":
    # Exemple population simulée
    population = [
        {"signal_type": "momentum", "rsi_buy": 30, "rsi_sell": 70, "weight": 1.0},
        {"signal_type": "breakout", "lookback_period": 20, "weight": 1.2},
        {"signal_type": "mean_reversion", "lookback_period": 20, "threshold": 0.02, "weight": 1.1},
    ]

    fitness_scores = [0.8, 0.6, 0.9]  # Simulé : chaque score est la performance d'une stratégie

    engine = StrategyEvolutionEngine(population)
    new_population = engine.evolve_population(fitness_scores)

    for i, strat in enumerate(new_population):
        print(f"Strategy {i+1}: {strat}")
