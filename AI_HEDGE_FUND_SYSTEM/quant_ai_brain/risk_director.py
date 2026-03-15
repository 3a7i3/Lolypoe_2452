class RiskDirector:
    def evaluate(self, strategy):
        if strategy["drawdown"] > 0.25:
            return "reject"
        return "accept"
