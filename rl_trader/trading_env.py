import numpy as np

class TradingEnv:
    def __init__(self, df):
        self.df = df
        self.step_index = 50
        self.position = 0
        self.balance = 1000

    def reset(self):
        self.step_index = 50
        self.position = 0
        self.balance = 1000
        return self._get_state()

    def _get_state(self):
        row = self.df.iloc[self.step_index]
        return np.array([
            row["close"],
            row["momentum"],
            row["volatility"]
        ])

    def step(self, action):
        price = self.df["close"].iloc[self.step_index]
        reward = 0
        if action == 1:  # buy
            self.position = 1
        elif action == 2:  # sell
            self.position = -1
        next_price = self.df["close"].iloc[self.step_index + 1]
        pnl = self.position * (next_price - price)
        reward = pnl
        self.balance += pnl
        self.step_index += 1
        done = self.step_index >= len(self.df) - 1
        return self._get_state(), reward, done
