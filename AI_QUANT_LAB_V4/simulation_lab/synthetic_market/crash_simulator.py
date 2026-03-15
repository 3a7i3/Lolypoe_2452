import random

class CrashSimulator:
    def inject_crash(self, df, magnitude=0.3):
        crash_index = random.randint(100, len(df)-100)
        df.loc[crash_index:, "close"] *= (1 - magnitude)
        return df
