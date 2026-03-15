class AlphaFeedbackEngine:
    def __init__(self):
        self.alphas = []

    def validate(self, strategy):
        return strategy['score'] > 0.5

    def update(self, strategy):
        if self.validate(strategy):
            self.alphas.append(strategy)
