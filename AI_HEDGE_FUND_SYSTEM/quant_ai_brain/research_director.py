class ResearchDirector:
    def decide_research(self, market_state):
        if market_state == "HIGH_VOLATILITY":
            return "search_volatility_strategies"
        if market_state == "TREND":
            return "search_momentum_strategies"
        return "general_alpha_search"
