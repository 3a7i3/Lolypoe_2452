# generator.py
class StrategyGenerator:
    def __init__(self, features, templates):
        self.features = features
        self.templates = templates

    def generate(self):
        """
        Génère des combinaisons de features et templates.
        Ex: momentum + volume spike, RSI + breakout, etc.
        """
        raise NotImplementedError
