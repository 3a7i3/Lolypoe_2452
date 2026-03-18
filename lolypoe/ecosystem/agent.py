import random

class TradingAgent:
    def __init__(self, strategy):
        self.strategy = strategy
        self.capital = 1000
        self.position = 0

    def decide(self, price, history):
        if self.strategy == "trend":
            if price > history[-1]:
                return "buy"
            else:
                return "sell"
        elif self.strategy == "mean_reversion":
            avg = sum(history[-10:]) / 10 if len(history) >= 10 else sum(history) / len(history)
            if price < avg:
                return "buy"
            else:
                return "sell"
        elif self.strategy == "random":
            return random.choice(["buy", "sell", "hold"])
        return "hold"
