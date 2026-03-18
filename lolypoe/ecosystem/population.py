import random
from ecosystem.agent import TradingAgent

class AgentPopulation:
    def __init__(self, size=100):
        self.agents = []
        strategies = ["trend", "mean_reversion", "random"]
        for _ in range(size):
            strat = random.choice(strategies)
            self.agents.append(TradingAgent(strat))
