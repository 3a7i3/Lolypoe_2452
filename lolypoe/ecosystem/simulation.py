from ecosystem.market import ArtificialMarket
from ecosystem.population import AgentPopulation
from ecosystem.evolution import EvolutionEngine

class EcosystemSimulation:
    def __init__(self):
        self.market = ArtificialMarket()
        self.population = AgentPopulation(100)
        self.evolution = EvolutionEngine()

    def run_step(self):
        buy_orders = 0
        sell_orders = 0
        for agent in self.population.agents:
            decision = agent.decide(self.market.price, self.market.history)
            if decision == "buy":
                buy_orders += 1
            elif decision == "sell":
                sell_orders += 1
        new_price = self.market.update_price(buy_orders, sell_orders)
        return new_price

    def run_generation(self, steps=100):
        for _ in range(steps):
            self.run_step()
        self.population.agents = self.evolution.evolve(self.population.agents)
