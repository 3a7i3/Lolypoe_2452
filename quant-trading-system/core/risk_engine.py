"""
Risk Engine - Advanced risk management and signal validation
"""

import logging
from typing import Dict, Optional
import config

logger = logging.getLogger(__name__)

class RiskEngine:
    """Advanced risk management system"""
    
    def __init__(self):
        self.daily_loss = 0.0
        self.portfolio_value = config.BACKTEST_INITIAL_CAPITAL
        self.max_drawdown_peak = config.BACKTEST_INITIAL_CAPITAL
        self.current_positions = 0
        logger.info("✓ Risk Engine initialized")
    
    async def validate_signal(self, symbol: str, action: str, confidence: float) -> bool:
        """
        Validate signal against risk parameters
        Returns: True if signal passes all risk checks
        """
        try:
            # Check 1: Confidence threshold
            if confidence < config.CONFIDENCE_THRESHOLD:
                return False
            
            # Check 2: Daily loss limit
            if self.daily_loss > config.MAX_DAILY_LOSS * self.portfolio_value:
                logger.warning("Daily loss limit exceeded")
                return False
            
            # Check 3: Drawdown limit
            if self._check_drawdown():
                logger.warning("Max drawdown exceeded")
                return False
            
            # Check 4: Max positions
            if action == 'BUY' and self.current_positions >= config.MAX_POSITIONS:
                logger.warning("Max positions reached")
                return False
            
            # Check 5: Market conditions
            if not self._check_market_conditions(symbol):
                return False
            
            # Check 6: Volatility check
            if not await self._check_volatility(symbol):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Signal validation error: {e}")
            return False
    
    def _check_drawdown(self) -> bool:
        """Check if drawdown exceeds limit"""
        try:
            current_drawdown = (self.max_drawdown_peak - self.portfolio_value) / self.max_drawdown_peak
            return current_drawdown > config.MAX_DRAWDOWN
        except Exception as e:
            logger.debug(f"Drawdown check error: {e}")
            return False
    
    def _check_market_conditions(self, symbol: str) -> bool:
        """Check if market conditions are suitable"""
        try:
            # Simplified market condition check
            # In production, would check volatility regime, liquidity, etc.
            return True
        except Exception as e:
            logger.debug(f"Market condition check error: {e}")
            return False
    
    async def _check_volatility(self, symbol: str) -> bool:
        """Check volatility is within acceptable range"""
        try:
            # Simplified volatility check
            return True
        except Exception as e:
            logger.debug(f"Volatility check error: {e}")
            return False
    
    async def check_position_risk(self, symbol: str, size: float, entry_price: float) -> bool:
        """Check if position size is within risk limits"""
        try:
            # Position size as % of portfolio
            position_pct = (size * entry_price) / self.portfolio_value
            
            if position_pct < config.MIN_POSITION_SIZE:
                logger.debug(f"Position size too small: {position_pct:.2%}")
                return False
            
            if position_pct > config.MAX_POSITION_SIZE:
                logger.warning(f"Position size too large: {position_pct:.2%}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Position risk check error: {e}")
            return False
    
    def update_portfolio_value(self, new_value: float):
        """Update portfolio value and track drawdown"""
        try:
            self.portfolio_value = new_value
            
            if new_value > self.max_drawdown_peak:
                self.max_drawdown_peak = new_value
            
        except Exception as e:
            logger.error(f"Portfolio value update error: {e}")
    
    def add_daily_loss(self, loss: float):
        """Track daily losses"""
        self.daily_loss += loss
    
    def reset_daily_loss(self):
        """Reset daily loss counter"""
        self.daily_loss = 0.0
    
    def update_position_count(self, delta: int):
        """Update open position count"""
        self.current_positions += delta
