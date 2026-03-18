import random

class TradingAgent:
    def __init__(self, strategy):
        self.strategy = strategy
        self.score = 0

    def trade(self, market):
        result = random.uniform(-1,1)
        self.score += result

class TradingEcosystem:
    def __init__(self):
        self.agents = []

    def populate(self, strategies):
        for s in strategies:
            self.agents.append(TradingAgent(s))

    def simulate(self, steps=100):
        for _ in range(steps):
            for agent in self.agents:
                agent.trade(None)

    def ranking(self):
        return sorted(self.agents, key=lambda x: x.score, reverse=True)
