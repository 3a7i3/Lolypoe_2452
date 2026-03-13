"""
Risk Enforcer Agent – Monitors and enforces risk limits
Prevents excessive positions, enforces stop-losses, triggers kill-switch
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class RiskEnforcer:
    """Agent that monitors and enforces risk policies"""

    def __init__(self, name: str = "RiskEnforcer", max_position_size: float = 0.10,
                 max_daily_loss: float = 0.05, max_portfolio_drawdown: float = 0.20):
        """Initialize risk enforcer"""
        self.name = name
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.max_portfolio_drawdown = max_portfolio_drawdown
        self.violations = []
        self.status = "ACTIVE"

    async def check_position_size(self, symbol: str, quantity: float, 
                                  price: float, portfolio_value: float) -> Dict:
        """Check if position size is within limits"""
        position_value = quantity * price
        position_pct = position_value / portfolio_value if portfolio_value > 0 else 0
        
        if position_pct > self.max_position_size:
            violation = {
                'type': 'POSITION_SIZE_EXCEEDED',
                'symbol': symbol,
                'position_pct': position_pct,
                'max_allowed': self.max_position_size,
                'action': 'REJECT'
            }
            self.violations.append(violation)
            logger.warning(f"⚠️ Position size violation: {symbol} {position_pct:.2%}")
            return {'allowed': False, 'reason': 'Position too large'}
        
        return {'allowed': True, 'position_pct': position_pct}

    async def check_daily_loss(self, daily_pnl: float, 
                              portfolio_value: float) -> Dict:
        """Check if daily loss exceeds limit"""
        daily_loss_pct = abs(daily_pnl) / portfolio_value if portfolio_value > 0 else 0
        
        if daily_loss_pct > self.max_daily_loss and daily_pnl < 0:
            violation = {
                'type': 'DAILY_LOSS_LIMIT_EXCEEDED',
                'daily_loss_pct': daily_loss_pct,
                'max_allowed': self.max_daily_loss,
                'action': 'STOP_TRADING'
            }
            self.violations.append(violation)
            self.status = "HALTED_LOSS"
            logger.error(f"❌ Daily loss limit hit: {daily_loss_pct:.2%}")
            return {'allowed': False, 'reason': 'Daily loss limit exceeded'}
        
        return {'allowed': True}

    async def check_portfolio_drawdown(self, current_drawdown: float) -> Dict:
        """Check portfolio drawdown against limit"""
        if current_drawdown < self.max_portfolio_drawdown:
            return {'allowed': True}
        else:
            violation = {
                'type': 'DRAWDOWN_EXCEEDED',
                'current_drawdown': current_drawdown,
                'max_allowed': self.max_portfolio_drawdown,
                'action': 'KILL_SWITCH'
            }
            self.violations.append(violation)
            self.status = "KILL_SWITCH_ACTIVE"
            logger.critical(f"🚨 KILL SWITCH TRIGGERED: Drawdown {current_drawdown:.2%}")
            return {'allowed': False, 'reason': 'Kill switch activated'}

    async def enforce_risk_policy(self, order: Dict, 
                                 portfolio_value: float,
                                 daily_pnl: float,
                                 current_drawdown: float) -> Dict:
        """Enforce all risk policies on an order"""
        
        # Check all risk constraints
        pos_check = await self.check_position_size(
            order['symbol'], order['amount'], order['price'], portfolio_value
        )
        
        if not pos_check['allowed']:
            return {'approved': False, 'reason': 'Position size limit'}
        
        loss_check = await self.check_daily_loss(daily_pnl, portfolio_value)
        if not loss_check['allowed']:
            return {'approved': False, 'reason': 'Daily loss limit'}
        
        dd_check = await self.check_portfolio_drawdown(current_drawdown)
        if not dd_check['allowed']:
            return {'approved': False, 'reason': 'Kill switch'}
        
        logger.info(f"✅ Risk check passed for {order['symbol']}")
        return {'approved': True}

    def get_status(self) -> Dict[str, Any]:
        """Get risk enforcer status"""
        return {
            'status': self.status,
            'violations_count': len(self.violations),
            'recent_violations': self.violations[-5:],
            'max_position_size': self.max_position_size,
            'max_daily_loss': self.max_daily_loss,
            'max_portfolio_drawdown': self.max_portfolio_drawdown
        }

    def reset(self):
        """Reset daily metrics"""
        self.violations = []
        if self.status == "HALTED_LOSS":
            self.status = "ACTIVE"
