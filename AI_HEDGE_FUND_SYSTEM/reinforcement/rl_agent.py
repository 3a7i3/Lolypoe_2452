import random

class RLTrader:
    actions = ["buy", "sell", "hold"]

    def choose_action(self):
        return random.choice(self.actions)

    def reward(self, pnl):
        return pnl
