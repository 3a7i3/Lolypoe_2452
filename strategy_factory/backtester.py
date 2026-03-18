from multiprocessing import Pool

class Backtester:
    def evaluate(self, strategy, df):
        pnl = 0
        for i in range(10, len(df)):
            if df["momentum"][i] > strategy["threshold"]:
                pnl += df["close"][i] - df["close"][i-1]
        return pnl

def run_parallel(strategies, df):
    backtester = Backtester()
    with Pool(8) as p:
        scores = p.starmap(backtester.evaluate, [(s, df) for s in strategies])
    return scores
