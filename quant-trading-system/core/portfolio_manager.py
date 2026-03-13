"""
Portfolio Manager - Intelligent portfolio optimization and position management
"""

import logging
from typing import Dict, List
import numpy as np
import config

logger = logging.getLogger(__name__)

class PortfolioManager:
    """Intelligent portfolio optimization and management"""
    
    def __init__(self):
        self.positions = {}
        self.allocations = {}
        self.total_capital = config.BACKTEST_INITIAL_CAPITAL
        logger.info("✓ Portfolio Manager initialized")
    
    async def optimize(self, valid_trades: List, method: str = 'kelly_criterion') -> Dict:
        """
        Optimize portfolio allocation
        Methods: kelly_criterion, risk_parity, mean_variance
        """
        try:
            if not valid_trades:
                return {}
            
            if method == 'kelly_criterion':
                return await self._optimize_kelly(valid_trades)
            elif method == 'risk_parity':
                return await self._optimize_risk_parity(valid_trades)
            else:
                return await self._optimize_mean_variance(valid_trades)
            
        except Exception as e:
            logger.error(f"Portfolio optimization error: {e}")
            return {}
    
    async def _optimize_kelly(self, valid_trades: List) -> Dict:
        """Kelly Criterion optimization"""
        try:
            optimized = {}
            total_confidence = sum(t.get('confidence', 0) for t in valid_trades)
            
            if total_confidence == 0:
                return {}
            
            available_capital = self.total_capital * config.ARBITRAGE_CAPITAL_ALLOCATION
            
            for trade in valid_trades[:config.MAX_POSITIONS]:
                kelly_fraction = trade.get('confidence', 0) / total_confidence
                position_size = available_capital * kelly_fraction * 0.5  # Half-Kelly
                
                optimized[trade['symbol']] = {
                    'action': trade['action'],
                    'size': position_size / trade.get('price', 100),  # Convert to coins
                    'confidence': trade['confidence'],
                    'kelly_fraction': kelly_fraction
                }
            
            self.allocations = optimized
            return optimized
            
        except Exception as e:
            logger.error(f"Kelly optimization error: {e}")
            return {}
    
    async def _optimize_risk_parity(self, valid_trades: List) -> Dict:
        """Risk Parity optimization"""
        try:
            optimized = {}
            num_trades = len(valid_trades)
            
            if num_trades == 0:
                return {}
            
            equal_allocation = self.total_capital / num_trades
            
            for trade in valid_trades[:config.MAX_POSITIONS]:
                optimized[trade['symbol']] = {
                    'action': trade['action'],
                    'size': equal_allocation / trade.get('price', 100),
                    'confidence': trade['confidence'],
                    'allocation': 1.0 / num_trades
                }
            
            self.allocations = optimized
            return optimized
            
        except Exception as e:
            logger.error(f"Risk parity optimization error: {e}")
            return {}
    
    async def _optimize_mean_variance(self, valid_trades: List) -> Dict:
        """Mean-Variance optimization"""
        try:
            # Simplified mean-variance
            optimized = {}
            
            # Weight by confidence
            total_confidence = sum(t.get('confidence', 0) for t in valid_trades)
            
            for trade in valid_trades[:config.MAX_POSITIONS]:
                weight = trade.get('confidence', 0) / total_confidence if total_confidence > 0 else 0
                position_size = self.total_capital * weight * config.MIN_POSITION_SIZE
                
                optimized[trade['symbol']] = {
                    'action': trade['action'],
                    'size': position_size / trade.get('price', 100),
                    'confidence': trade['confidence'],
                    'weight': weight
                }
            
            self.allocations = optimized
            return optimized
            
        except Exception as e:
            logger.error(f"Mean-variance optimization error: {e}")
            return {}
    
    async def monitor_positions(self, market_data: Dict) -> Dict:
        """Monitor and manage active positions"""
        try:
            updated_positions = {}
            
            for symbol, position in self.positions.items():
                try:
                    current_price = market_data.get(symbol, {}).get('price', 0)
                    
                    if current_price == 0:
                        continue
                    
                    pnl = (current_price - position['entry_price']) * position['quantity']
                    pnl_pct = (current_price - position['entry_price']) / position['entry_price']
                    
                    # Check stop-loss and take-profit
                    should_close = False
                    reason = None
                    
                    if pnl_pct <= -config.STOP_LOSS_PERCENT / 100:
                        should_close = True
                        reason = "Stop-loss hit"
                    elif pnl_pct >= config.TAKE_PROFIT_PERCENT / 100:
                        should_close = True
                        reason = "Take-profit hit"
                    
                    position['current_price'] = current_price
                    position['pnl'] = pnl
                    position['pnl_pct'] = pnl_pct
                    position['should_close'] = should_close
                    position['close_reason'] = reason
                    
                    updated_positions[symbol] = position
                    
                except Exception as e:
                    logger.debug(f"Position monitoring error for {symbol}: {e}")
                    continue
            
            self.positions = updated_positions
            return updated_positions
            
        except Exception as e:
            logger.error(f"Position monitoring error: {e}")
            return {}
    
    def add_position(self, symbol: str, action: str, quantity: float, entry_price: float):
        """Add new position"""
        try:
            self.positions[symbol] = {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': entry_price,
                'pnl': 0,
                'pnl_pct': 0,
                'timestamp': None,
                'should_close': False
            }
            logger.info(f"Position added: {symbol} {action} {quantity} @ {entry_price}")
        except Exception as e:
            logger.error(f"Add position error: {e}")
    
    def close_position(self, symbol: str):
        """Close position"""
        try:
            if symbol in self.positions:
                del self.positions[symbol]
                logger.info(f"Position closed: {symbol}")
        except Exception as e:
            logger.error(f"Close position error: {e}")
