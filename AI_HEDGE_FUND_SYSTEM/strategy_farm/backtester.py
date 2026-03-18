import operator

class StrategyBacktester:
    op_map = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le
    }

    def test(self, strategy, df, initial_capital=1000):
        trades = []
        capital = initial_capital
        pos_size = strategy.get("position_size", 0.1)
        conds = strategy.get("conditions", [])
        logic = strategy.get("logic", "AND")
        for i in range(1, len(df)):
            results = []
            for cond in conds:
                ind = cond["indicator"]
                op = self.op_map.get(cond.get("operator", ">"), operator.gt)
                threshold = cond["threshold"]
                val = df[ind][i]
                results.append(op(val, threshold))
            signal = all(results) if logic == "AND" else any(results)
            if signal:
                entry = df["close"][i-1]
                exit = df["close"][i]
                trade_cap = capital * pos_size
                pnl = (exit - entry) * (trade_cap / entry)
                trades.append({
                    "pnl": pnl,
                    "entry": entry,
                    "exit": exit,
                    "size": trade_cap
                })
                capital += pnl
        return trades
