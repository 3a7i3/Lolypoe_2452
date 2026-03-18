# Evolution Engine — Niveau 2
import random

class EvolutionEngine:
    def select(self, population, n_best=2):
        # Sélectionne les n meilleures stratégies
        return sorted(population, key=lambda x: -x["score"])[:n_best]

    def mutate(self, strategy):
        # Mutation simple : modifie légèrement la règle
        new_rule = strategy["rule"] + f"+{random.uniform(-0.1,0.1):.2f}"
        return {"id": strategy["id"]+"m", "rule": new_rule, "score": None}

    def crossover(self, parent1, parent2):
        # Combine deux règles (très simplifié)
        rule = parent1["rule"] + "|" + parent2["rule"]
        return {"id": parent1["id"]+parent2["id"], "rule": rule, "score": None}

    def next_generation(self, selected):
        # Crée une nouvelle génération par mutation et crossover
        children = []
        for s in selected:
            children.append(self.mutate(s))
        if len(selected) > 1:
            children.append(self.crossover(selected[0], selected[1]))
        return children
