class RegimeSimulator:
    regimes = {
        "bull": {"drift": 0.001, "volatility": 0.02},
        "bear": {"drift": -0.001, "volatility": 0.025},
        "sideways": {"drift": 0, "volatility": 0.01}
    }
    def get_params(self, regime):
        return self.regimes[regime]
