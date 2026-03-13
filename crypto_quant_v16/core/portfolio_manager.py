"""
Portfolio Manager – Dynamic allocation with Kelly Criterion
Manages multi-asset portfolio with risk-weighted sizing
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manage and optimize portfolio allocation"""

    def __init__(self, initial_capital: float = 10000.0, max_exposure: float = 0.95):
        """Initialize portfolio"""
        self.capital = initial_capital
        self.max_exposure = max_exposure
        self.positions = {}
        self.allocation = {}

    def kelly_allocation(self, win_rate: float, profit_factor: float, 
                        max_allocation: float = 0.25) -> float:
        """Calculate Kelly Criterion allocation"""
        if profit_factor <= 0:
            return 0
        kelly = (win_rate * profit_factor - (1 - win_rate)) / profit_factor
        kelly = max(0, min(kelly, max_allocation))  # Cap at max_allocation
        return kelly

    def allocate_equal_weight(self, symbols: List[str]) -> Dict[str, float]:
        """Simple equal-weight allocation"""
        if not symbols:
            return {}
        weight = 1.0 / len(symbols)
        return {symbol: weight for symbol in symbols}

    def allocate_risk_weighted(self, df: pd.DataFrame, 
                              risk_metric: str = 'volatility') -> Dict[str, float]:
        """Allocate inversely to volatility (lower vol = higher allocation)"""
        if df.empty:
            return {}

        if risk_metric == 'volatility':
            df['weight'] = 1.0 / (df['volatility'] + 0.01)
        else:
            df['weight'] = 1.0 / (df[risk_metric] + 0.01)

        df['weight'] = df['weight'] / df['weight'].sum()
        
        allocation = {}
        for _, row in df.iterrows():
            allocation[row['symbol']] = min(row['weight'], self.max_exposure / len(df))

        return allocation

    def update_position(self, symbol: str, quantity: float, entry_price: float):
        """Update a position"""
        self.positions[symbol] = {
            'quantity': quantity,
            'entry_price': entry_price,
            'entry_time': pd.Timestamp.now()
        }
        logger.info(f"✅ Position updated: {symbol} {quantity} @ {entry_price}")

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        value = 0
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                value += pos['quantity'] * current_prices[symbol]
        value += self.capital - sum(pos['quantity'] * pos['entry_price'] 
                                    for pos in self.positions.values())
        return value

    def get_pnl(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """Calculate P&L"""
        pnl_dict = {}
        total_pnl = 0
        
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                pnl = (current_price - pos['entry_price']) * pos['quantity']
                pnl_pct = ((current_price - pos['entry_price']) / pos['entry_price'] * 100)
                pnl_dict[symbol] = {
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'current_price': current_price,
                    'entry_price': pos['entry_price']
                }
                total_pnl += pnl

        return {
            'positions': pnl_dict,
            'total_pnl': total_pnl,
            'total_pnl_pct': (total_pnl / self.capital * 100) if self.capital > 0 else 0
        }

    def rebalance(self, target_allocation: Dict[str, float], 
                 current_prices: Dict[str, float]):
        """Rebalance portfolio to target allocation"""
        logger.info(f"🔄 Rebalancing portfolio: {target_allocation}")
        # Implementation would execute trades
        self.allocation = target_allocation
        return True
