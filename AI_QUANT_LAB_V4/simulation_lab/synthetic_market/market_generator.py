import numpy as np
import pandas as pd

class MarketGenerator:
    def generate_price_series(self, length=1000, start_price=10000, drift=0.0005, volatility=0.02):
        prices = [start_price]
        for _ in range(length):
            shock = np.random.normal(drift, volatility)
            new_price = prices[-1] * (1 + shock)
            prices.append(new_price)
        df = pd.DataFrame({"close": prices})
        return df
