class Backtester:
    def run(self, strategy, df):
        pnl = 0
        for i in range(10,len(df)):
            if strategy["indicator"] == "momentum":
                if df["momentum"][i] > strategy["threshold"]:
                    pnl += df["close"][i] - df["close"][i-1]
        return pnl
