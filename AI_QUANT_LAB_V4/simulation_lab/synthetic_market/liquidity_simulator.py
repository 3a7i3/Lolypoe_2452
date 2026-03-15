import random

class LiquidityCrisis:
    def simulate(self, df):
        start = random.randint(100, len(df)-100)
        df.loc[start:start+30, "close"] *= 0.85
        return df
