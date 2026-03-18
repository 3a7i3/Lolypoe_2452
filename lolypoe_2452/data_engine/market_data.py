import pandas as pd
import numpy as np

class MarketData:
    def load_dummy(self, n=1000):
        prices = np.cumsum(np.random.randn(n)) + 100
        df = pd.DataFrame({
            "close": prices
        })
        return df
