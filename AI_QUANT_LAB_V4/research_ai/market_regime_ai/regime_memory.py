class RegimeMemory:
    def __init__(self):
        self.history = []
    def record(self, regime):
        self.history.append(regime)
    def last(self):
        if self.history:
            return self.history[-1]
        return None
