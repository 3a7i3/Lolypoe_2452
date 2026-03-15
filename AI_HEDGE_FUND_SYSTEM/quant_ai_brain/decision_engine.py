class DecisionEngine:
    def decide(self, data):
        decisions = {}
        if data["volatility"] > 0.05:
            decisions["mode"] = "defensive"
        else:
            decisions["mode"] = "aggressive"
        return decisions
