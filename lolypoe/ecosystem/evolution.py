import random

class EvolutionEngine:
    def evolve(self, agents):
        agents.sort(key=lambda a: a.capital, reverse=True)
        survivors = agents[:len(agents)//2]
        new_agents = []
        for a in survivors:
            new_agents.append(a)
            if random.random() < 0.3:
                new_agents.append(type(a)(a.strategy))
        return new_agents
