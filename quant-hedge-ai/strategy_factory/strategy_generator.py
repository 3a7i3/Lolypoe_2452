from __future__ import annotations

from dataclasses import dataclass

from agents.strategy.genetic_optimizer import GeneticOptimizer
from agents.strategy.strategy_generator import StrategyGenerator


@dataclass
class GeneratorConfig:
    population_size: int = 120
    generations: int = 2


class FactoryStrategyGenerator:
    """Creates and evolves candidate strategies for the Strategy Factory."""

    def __init__(self, cfg: GeneratorConfig | None = None) -> None:
        self.cfg = cfg or GeneratorConfig()
        self._base = StrategyGenerator()
        self._optimizer = GeneticOptimizer()

    def generate_candidates(self, population_size: int | None = None, generations: int | None = None) -> list[dict]:
        n = max(1, int(population_size or self.cfg.population_size))
        g = max(1, int(generations or self.cfg.generations))
        population = self._base.generate_population(n)
        return self._optimizer.evolve(population, generations=g)
