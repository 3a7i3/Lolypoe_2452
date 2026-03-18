import numpy as np
import pandas as pd

class AdvancedBacktester:

    def __init__(self):
        pass

    def run(self, strategy, df):
        """
        Exécute le backtest complet d'une stratégie sur un DataFrame df
        """
        trades = []
        equity = [1000]  # capital initial
        position = 0

        for i in range(strategy["lookback"], len(df)):

            # Exemple pour momentum
            signal = 0
            if strategy["indicator"] == "momentum":
                if df["momentum"][i] > strategy["threshold"]:
                    signal = 1  # buy
                elif df["momentum"][i] < -strategy["threshold"]:
                    signal = -1  # sell

            # Execution du trade
            pnl = position * (df["close"][i] - df["close"][i-1])
            equity.append(equity[-1] + pnl)

            if signal != 0:
                position = signal  # on prend position
                trades.append({
                    "index": i,
                    "signal": signal,
                    "price": df["close"][i],
                    "pnl": pnl
                })

        return {
            "equity_curve": np.array(equity),
            "trades": trades,
            "metrics": self.compute_metrics(np.array(equity), trades)
        }

    def compute_metrics(self, equity_curve, trades):
        """
        Calcule Sharpe, max drawdown, winrate, profit factor
        """
        returns = np.diff(equity_curve) / equity_curve[:-1]
        sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
        max_dd = self.max_drawdown(equity_curve)

        wins = [t["pnl"] for t in trades if t["pnl"] > 0]
        losses = [t["pnl"] for t in trades if t["pnl"] < 0]

        winrate = len(wins) / len(trades) if trades else 0
        profit_factor = (sum(wins) / (-sum(losses) + 1e-8)) if losses else float('inf')

        return {
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "winrate": winrate,
            "profit_factor": profit_factor,
            "total_pnl": equity_curve[-1] - equity_curve[0]
        }

    def max_drawdown(self, equity_curve):
        peak = equity_curve[0]
        max_dd = 0
        for v in equity_curve:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd
