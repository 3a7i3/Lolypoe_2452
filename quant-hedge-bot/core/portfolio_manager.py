"""
Portfolio Manager - Gestion du portefeuille
"""

import pandas as pd
import numpy as np
from config import INITIAL_CAPITAL, ALLOCATION_STRATEGY, MAX_POSITION_SIZE, MIN_POSITION_SIZE
from config import REBALANCE_FREQUENCY
from utils.logger import logger

class PortfolioManager:
    """Gere le portefeuille d'investissement."""
    
    def __init__(self, capital=INITIAL_CAPITAL):
        self.capital = capital
        self.positions = {}  # {symbol: {'quantity': X, 'entry_price': Y, ...}}
        self.cash = capital
        self.allocation_strategy = ALLOCATION_STRATEGY
    
    def calculate_portfolio_weights(self, market_data, signals):
        """Calcule les poids du portefeuille."""
        weights = {}
        
        if self.allocation_strategy == 'equal':
            # Egal pour tous les BUY signals
            buy_signals = sum(1 for s in signals.values() if s == 'BUY')
            for symbol, signal in signals.items():
                if signal == 'BUY':
                    weights[symbol] = 1.0 / buy_signals if buy_signals > 0 else 0
                else:
                    weights[symbol] = 0
        
        elif self.allocation_strategy == 'risk-parity':
            # Allocation basee sur la volatilite
            volatilities = {}
            for symbol, data in market_data.items():
                if 'Volatility' in data.columns:
                    volatilities[symbol] = data['Volatility'].iloc[-1]
                else:
                    volatilities[symbol] = 0.01
            
            buy_symbols = [s for s, sig in signals.items() if sig == 'BUY']
            total_vol = sum(volatilities.get(s, 0) for s in buy_symbols)
            
            for symbol in buy_symbols:
                weights[symbol] = (1 - volatilities.get(symbol, 0) / total_vol) if total_vol > 0 else 0
        
        elif self.allocation_strategy == 'momentum':
            # Allocation basee sur le momentum
            momentum_scores = {}
            for symbol, data in market_data.items():
                close_col = 'Close'
                if close_col in data.columns and len(data) >= 20:
                    momentum = (data[close_col].iloc[-1] - data[close_col].iloc[-20]) / data[close_col].iloc[-20]
                    momentum_scores[symbol] = momentum
                else:
                    momentum_scores[symbol] = 0
            
            buy_symbols = [s for s, sig in signals.items() if sig == 'BUY']
            total_momentum = sum(momentum_scores.get(s, 0) for s in buy_symbols)
            
            for symbol in buy_symbols:
                weights[symbol] = momentum_scores.get(symbol, 0) / total_momentum if total_momentum > 0 else 0
        
        return weights
    
    def allocate_capital(self, weights):
        """Alloue le capital basé sur les poids."""
        allocations = {}
        for symbol, weight in weights.items():
            allocation = self.capital * weight
            # Limiter taille position
            allocation = min(allocation, self.capital * MAX_POSITION_SIZE)
            allocation = max(allocation, self.capital * MIN_POSITION_SIZE)
            allocations[symbol] = allocation
        
        return allocations
    
    def update_position(self, symbol, quantity, entry_price, current_price):
        """Met a jour une position."""
        if quantity > 0:
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': current_price,
                'pnl': (current_price - entry_price) * quantity,
                'pnl_percent': ((current_price - entry_price) / entry_price) * 100
            }
        elif symbol in self.positions:
            del self.positions[symbol]
    
    def get_total_portfolio_value(self):
        """Calcule la valeur totale du portefeuille."""
        positions_value = sum(p['quantity'] * p['current_price'] for p in self.positions.values())
        return self.cash + positions_value
    
    def get_portfolio_allocation(self):
        """Retourne la répartition actuelle."""
        total_value = self.get_total_portfolio_value()
        allocation = {}
        
        for symbol, position in self.positions.items():
            value = position['quantity'] * position['current_price']
            allocation[symbol] = (value / total_value) * 100
        
        allocation['cash'] = (self.cash / total_value) * 100
        return allocation
    
    def get_portfolio_stats(self):
        """Retourne les stats du portefeuille."""
        total_value = self.get_total_portfolio_value()
        initial_value = self.capital
        total_pnl = total_value - initial_value
        total_pnl_percent = (total_pnl / initial_value) * 100
        
        positions_pnl = sum(p.get('pnl', 0) for p in self.positions.values())
        
        return {
            'total_value': total_value,
            'initial_value': initial_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'positions_pnl': positions_pnl,
            'num_positions': len(self.positions),
            'cash': self.cash
        }
