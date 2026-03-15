import numpy as np

def annualized_sharpe(returns, periods=252):
    return np.sqrt(periods) * returns.mean() / (returns.std() + 1e-9)

def max_drawdown(equity_curve):
    roll_max = equity_curve.cummax()
    drawdown = (roll_max - equity_curve) / roll_max
    return drawdown.max()
