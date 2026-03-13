from __future__ import annotations

import random


class GeneticOptimizer:
    """Simple mutate/crossover loop for candidate strategies."""

    def mutate(self, strategy: dict) -> dict:
        child = dict(strategy)
        child["period"] = max(2, int(child.get("period", 20)) + random.randint(-8, 8))
        child["threshold"] = round(max(0.1, float(child.get("threshold", 1.0)) + random.uniform(-0.2, 0.2)), 3)
        return child

    def crossover(self, a: dict, b: dict) -> dict:
        return {
            "entry_indicator": random.choice([a.get("entry_indicator"), b.get("entry_indicator")]),
            "exit_indicator": random.choice([a.get("exit_indicator"), b.get("exit_indicator")]),
            "period": random.choice([a.get("period"), b.get("period")]),
            "threshold": random.choice([a.get("threshold"), b.get("threshold")]),
            "timeframe": random.choice([a.get("timeframe"), b.get("timeframe")]),
        }

    def evolve(self, population: list[dict], generations: int = 3) -> list[dict]:
        if not population:
            return []
        current = list(population)
        for _ in range(max(1, generations)):
            random.shuffle(current)
            next_gen = []
            for i in range(0, len(current), 2):
                a = current[i]
                b = current[(i + 1) % len(current)]
                child = self.crossover(a, b)
                if random.random() < 0.8:
                    child = self.mutate(child)
                next_gen.append(child)
            current.extend(next_gen)
            current = current[: len(population)]
        return current
