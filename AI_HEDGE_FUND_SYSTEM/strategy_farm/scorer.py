import math

class StrategyScorer:
    def score(self, trades):
        if len(trades) == 0:
            return 0
        pnls = [t["pnl"] for t in trades]
        pnl = sum(pnls)
        winrate = sum(1 for t in trades if t["pnl"] > 0) / len(trades)
        # Sharpe ratio (simplifié, sans risk-free)
        mean = pnl / len(trades)
        std = math.sqrt(sum((x - mean) ** 2 for x in pnls) / len(trades)) if len(trades) > 1 else 1
        sharpe = mean / std if std != 0 else 0
        # Max drawdown
        equity = 0
        peak = 0
        max_dd = 0
        for t in pnls:
            equity += t
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
        # Score composite
        score = pnl * winrate + sharpe * 2 - max_dd * 0.5
        return score
