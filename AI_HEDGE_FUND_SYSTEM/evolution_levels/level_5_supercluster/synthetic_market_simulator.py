# Niveau 5 — SyntheticMarketSimulator
import numpy as np

class SyntheticMarketSimulator:
    def generate(self, prices, regime="normal"):
        if regime == "flash_crash":
            noise = np.random.normal(-0.2, 0.05, len(prices))
        elif regime == "bull_run":
            noise = np.random.normal(0.05, 0.02, len(prices))
        elif regime == "low_liquidity":
            noise = np.random.normal(0, 0.05, len(prices))
        elif regime == "hyper_volatility":
            noise = np.random.normal(0, 0.1, len(prices))
        else:
            noise = np.random.normal(0, 0.02, len(prices))
        return prices * (1 + noise)
