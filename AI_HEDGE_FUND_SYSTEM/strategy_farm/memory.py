import json
import os

class StrategyMemory:
    def __init__(self, path="strategy_memory.json"):
        self.path = path
        self.strategies_db = []
        self.load()

    def store(self, strategy, score):
        self.strategies_db.append({
            "strategy": strategy,
            "score": score
        })
        self.save()

    def get_top(self, n=10):
        return sorted(self.strategies_db, key=lambda x: x["score"], reverse=True)[:n]

    def save(self):
        try:
            with open(self.path, "w") as f:
                json.dump(self.strategies_db, f, indent=2)
        except Exception as e:
            print(f"[StrategyMemory] Save error: {e}")

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    self.strategies_db = json.load(f)
            except Exception as e:
                print(f"[StrategyMemory] Load error: {e}")
