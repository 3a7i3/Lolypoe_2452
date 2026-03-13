"""Analytics module for dashboard"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_portfolio_metrics():
    """Get portfolio metrics"""
    return {
        'aum': 1234567.89,
        'daily_pnl': 12345.67,
        'sharpe_ratio': 1.85,
        'max_drawdown': -0.085,
        'win_rate': 0.625,
        'total_trades': 214
    }

def get_strategy_performance():
    """Get strategy performance metrics"""
    return {
        'trend_following': {'sharpe': 1.85, 'win_rate': 0.625},
        'mean_reversion': {'sharpe': 1.45, 'win_rate': 0.582},
        'breakout': {'sharpe': 2.10, 'win_rate': 0.723},
        'volatility': {'sharpe': 1.20, 'win_rate': 0.551},
        'momentum': {'sharpe': 1.75, 'win_rate': 0.645},
        'stat_arb': {'sharpe': 0.95, 'win_rate': 0.420}
    }

def get_portfolio_allocation():
    """Get current portfolio allocation"""
    return {
        'BTC/USDT': 0.35,
        'ETH/USDT': 0.20,
        'SOL/USDT': 0.15,
        'ADA/USDT': 0.20,
        'XRP/USDT': 0.10
    }
