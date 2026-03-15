import random

class WhaleManipulation:
    def pump_dump(self, df):
        start = random.randint(50, len(df)-200)
        pump = 1.2
        dump = 0.7
        df.loc[start:start+20, "close"] *= pump
        df.loc[start+21:start+50, "close"] *= dump
        return df
