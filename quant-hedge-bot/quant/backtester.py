"""
Backtester - Backtesting de strategies
"""

import numpy as np
import pandas as pd
from config import BACKTEST_CAPITAL, BACKTEST_COMMISSION, BACKTEST_SLIPPAGE
from utils.logger import logger

class Backtester:
    """Effectue le backtesting de strategies."""
    
    def __init__(self, initial_capital=BACKTEST_CAPITAL):
        self.capital = initial_capital
        self.position = False
        self.entry_price = 0
        self.trades = []
        self.equity_curve = [initial_capital]
    
    def run_backtest(self, data, strategy_func):
        """Execute un backtest complet."""
        logger.info("Demarrage du backtest...")
        
        for i in range(1, len(data)):
            current_data = data.iloc[:i+1]
            signal = strategy_func(current_data)
            current_price = data['Close'].iloc[i]
            
            # BUY
            if signal == "BUY" and not self.position:
                self.entry_price = current_price * (1 + BACKTEST_SLIPPAGE)
                self.position = True
                self.trades.append({
                    'type': 'BUY',
                    'price': self.entry_price,
                    'time': data.index[i]
                })
            
            # SELL
            elif signal == "SELL" and self.position:
                exit_price = current_price * (1 - BACKTEST_SLIPPAGE)
                pnl = (exit_price - self.entry_price) / self.entry_price
                commission = abs(pnl) * BACKTEST_COMMISSION
                net_pnl = pnl - commission
                
                self.capital *= (1 + net_pnl)
                self.position = False
                
                self.trades.append({
                    'type': 'SELL',
                    'price': exit_price,
                    'pnl': net_pnl,
                    'time': data.index[i]
                })
            
            self.equity_curve.append(self.capital)
        
        return self.get_backtest_results()
    
    def get_backtest_results(self):
        """Retourne les resultats du backtest."""
        equity_array = np.array(self.equity_curve)
        total_return = ((self.capital - BACKTEST_CAPITAL) / BACKTEST_CAPITAL) * 100
        
        # Max drawdown
        max_equity = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - max_equity) / max_equity
        max_drawdown = np.min(drawdown) * 100
        
        # Win rate
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']
        winning_trades = len([t for t in sell_trades if t.get('pnl', 0) > 0])
        win_rate = (winning_trades / len(sell_trades) * 100) if len(sell_trades) > 0 else 0
        
        return {
            'initial_capital': BACKTEST_CAPITAL,
            'final_capital': float(self.capital),
            'total_return_percent': float(total_return),
            'max_drawdown_percent': float(max_drawdown),
            'num_trades': len([t for t in self.trades if t['type'] == 'SELL']),
            'winning_trades': winning_trades,
            'win_rate': float(win_rate),
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
