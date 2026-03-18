class BacktestAgent:
    def evaluate(self, strategies, df):
        print("[BacktestAgent] Evaluating strategies...")
        results = []
        for s in strategies:
            score = self.run_backtest(s, df)
            results.append({"strategy": s, "score": score, "drawdown": 0.1})
        return results

    def run_backtest(self, strategy, df):
        print(f"  [BacktestAgent] Backtesting {strategy}")
        return 1.0
