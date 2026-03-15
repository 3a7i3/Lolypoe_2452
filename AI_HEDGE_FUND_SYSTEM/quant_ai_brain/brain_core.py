class QuantAIBrain:
    def __init__(self):
        self.research = None
        self.strategy = None
        self.risk = None
        self.portfolio = None
        self.learning = None

    def connect_modules(self, research, strategy, risk, portfolio, learning):
        self.research = research
        self.strategy = strategy
        self.risk = risk
        self.portfolio = portfolio
        self.learning = learning
