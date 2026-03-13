"""
Risk Limits & Emergency Shutdown
Enforce trading boundaries and protect capital
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """Risk limit configuration"""
    max_position_size_pct: float = 0.1  # 10% of portfolio per position
    max_daily_loss_pct: float = 0.05  # Max 5% daily loss
    max_total_loss_pct: float = 0.2  # Max 20% total loss
    max_positions: int = 20  # Max concurrent positions
    max_leverage: float = 1.0  # No leverage by default
    max_single_trade_loss: float = 10000  # Max loss per trade
    position_size_limit: float = 5000  # Max position size in USD
    drawdown_limit: float = 0.15  # Max 15% drawdown
    

class RiskManager:
    """Enforce risk limits and manage portfolio risk"""
    
    def __init__(self, risk_limits: RiskLimits, initial_balance: float):
        self.limits = risk_limits
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.peak_balance = initial_balance
        self.daily_pnl = 0.0
        self.positions: Dict[str, Dict] = {}
        self.daily_reset_time = datetime.now()
        self.is_trading_allowed = True
        self.shutdown_triggered = False
        self.violations: List[str] = []
        
        logger.info(f"Risk Manager initialized: Balance=${initial_balance:,.2f}")
    
    def update_balance(self, new_balance: float):
        """Update current balance"""
        pnl = new_balance - self.current_balance
        self.daily_pnl += pnl
        self.current_balance = new_balance
        
        # Update peak
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance
    
    def can_place_trade(self, trade: Dict) -> tuple[bool, Optional[str]]:
        """Check if trade is allowed"""
        self.violations.clear()
        
        # Reset daily limits if needed
        self._check_daily_reset()
        
        # Check if trading is allowed
        if not self.is_trading_allowed:
            return False, "Trading is currently suspended"
        
        if self.shutdown_triggered:
            return False, "Emergency shutdown triggered"
        
        # Check daily loss limit
        daily_loss_pct = abs(self.daily_pnl) / self.initial_balance
        if daily_loss_pct > self.limits.max_daily_loss_pct:
            return False, f"Daily loss limit exceeded: {daily_loss_pct:.2%}"
        
        # Check total loss limit
        total_loss = self.initial_balance - self.current_balance
        total_loss_pct = total_loss / self.initial_balance if self.initial_balance > 0 else 0
        if total_loss_pct > self.limits.max_total_loss_pct:
            return False, f"Total loss limit exceeded: {total_loss_pct:.2%}"
        
        # Check max positions
        if len(self.positions) >= self.limits.max_positions:
            return False, f"Maximum positions reached: {self.limits.max_positions}"
        
        # Check position size
        trade_size = trade.get('quantity', 0) * trade.get('price', 0)
        if trade_size > self.limits.position_size_limit:
            return False, f"Trade size exceeds limit: ${trade_size:,.0f} > ${self.limits.position_size_limit:,.0f}"
        
        # Check position size as % of portfolio
        position_pct = trade_size / self.current_balance if self.current_balance > 0 else 0
        if position_pct > self.limits.max_position_size_pct:
            return False, f"Position size exceeds limit: {position_pct:.2%} > {self.limits.max_position_size_pct:.2%}"
        
        # Check max single trade loss
        estimated_loss = trade.get('estimated_loss', 0)
        if estimated_loss > self.limits.max_single_trade_loss:
            return False, f"Potential loss exceeds limit: ${estimated_loss:,.0f} > ${self.limits.max_single_trade_loss:,.0f}"
        
        # Check drawdown
        drawdown = (self.peak_balance - self.current_balance) / self.peak_balance if self.peak_balance > 0 else 0
        if drawdown > self.limits.drawdown_limit:
            return False, f"Drawdown limit exceeded: {drawdown:.2%} > {self.limits.drawdown_limit:.2%}"
        
        return True, None
    
    def register_position(self, symbol: str, quantity: float, entry_price: float):
        """Register open position"""
        self.positions[symbol] = {
            'quantity': quantity,
            'entry_price': entry_price,
            'current_price': entry_price,
            'entry_time': datetime.now(),
            'pnl': 0.0
        }
        logger.info(f"Position registered: {symbol} {quantity}@${entry_price}")
    
    def close_position(self, symbol: str):
        """Close position"""
        if symbol in self.positions:
            del self.positions[symbol]
            logger.info(f"Position closed: {symbol}")
    
    def update_position_price(self, symbol: str, current_price: float):
        """Update position current price"""
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos['current_price'] = current_price
            pos['pnl'] = (current_price - pos['entry_price']) * pos['quantity']
    
    def _check_daily_reset(self):
        """Reset daily limits if new day"""
        now = datetime.now()
        if now.date() != self.daily_reset_time.date():
            self.daily_pnl = 0.0
            self.daily_reset_time = now
            logger.info("Daily limits reset")
    
    def get_portfolio_risk(self) -> Dict[str, Any]:
        """Get portfolio risk metrics"""
        total_position_value = sum(
            pos['quantity'] * pos['current_price']
            for pos in self.positions.values()
        )
        
        total_pnl = sum(pos['pnl'] for pos in self.positions.values())
        
        drawdown = (self.peak_balance - self.current_balance) / self.peak_balance if self.peak_balance > 0 else 0
        daily_loss_pct = abs(self.daily_pnl) / self.initial_balance if self.initial_balance > 0 else 0
        total_loss = self.initial_balance - self.current_balance
        total_loss_pct = total_loss / self.initial_balance if self.initial_balance > 0 else 0
        
        return {
            'current_balance': self.current_balance,
            'initial_balance': self.initial_balance,
            'peak_balance': self.peak_balance,
            'total_position_value': total_position_value,
            'open_positions': len(self.positions),
            'total_pnl': total_pnl,
            'daily_pnl': self.daily_pnl,
            'drawdown': drawdown,
            'drawdown_pct': f"{drawdown:.2%}",
            'daily_loss_pct': f"{daily_loss_pct:.2%}",
            'total_loss_pct': f"{total_loss_pct:.2%}",
            'trading_allowed': self.is_trading_allowed,
            'emergency_shutdown': self.shutdown_triggered
        }
    
    async def trigger_emergency_shutdown(self, reason: str):
        """Trigger emergency shutdown"""
        logger.critical(f"🚨 EMERGENCY SHUTDOWN TRIGGERED: {reason}")
        self.shutdown_triggered = True
        self.is_trading_allowed = False
        
        # Close all positions
        await self.close_all_positions()
    
    async def close_all_positions(self):
        """Close all open positions"""
        logger.warning(f"Closing all {len(self.positions)} positions")
        symbols_to_close = list(self.positions.keys())
        for symbol in symbols_to_close:
            self.close_position(symbol)
        logger.info("All positions closed")
    
    def get_risk_alerts(self) -> list[Dict[str, Any]]:
        """Get risk alerts"""
        alerts = []
        
        # Check each limit
        daily_loss_pct = abs(self.daily_pnl) / self.initial_balance if self.initial_balance > 0 else 0
        if daily_loss_pct > self.limits.max_daily_loss_pct * 0.8:  # 80% of limit
            alerts.append({
                'severity': 'WARNING',
                'type': 'daily_loss',
                'message': f'Daily loss approaching limit: {daily_loss_pct:.2%}',
                'threshold': self.limits.max_daily_loss_pct
            })
        
        total_loss_pct = (self.initial_balance - self.current_balance) / self.initial_balance if self.initial_balance > 0 else 0
        if total_loss_pct > self.limits.max_total_loss_pct * 0.8:
            alerts.append({
                'severity': 'CRITICAL',
                'type': 'total_loss',
                'message': f'Total loss approaching limit: {total_loss_pct:.2%}',
                'threshold': self.limits.max_total_loss_pct
            })
        
        drawdown = (self.peak_balance - self.current_balance) / self.peak_balance if self.peak_balance > 0 else 0
        if drawdown > self.limits.drawdown_limit * 0.8:
            alerts.append({
                'severity': 'WARNING',
                'type': 'drawdown',
                'message': f'Drawdown approaching limit: {drawdown:.2%}',
                'threshold': self.limits.drawdown_limit
            })
        
        if len(self.positions) >= self.limits.max_positions * 0.9:
            alerts.append({
                'severity': 'INFO',
                'type': 'positions',
                'message': f'Approaching max positions: {len(self.positions)}/{self.limits.max_positions}',
                'threshold': self.limits.max_positions
            })
        
        return alerts


class RiskMonitor:
    """Continuous risk monitoring"""
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.is_monitoring = False
        self.callbacks: Dict[str, Callable] = {}
    
    def on_alert(self, callback: Callable):
        """Register alert callback"""
        self.callbacks['alert'] = callback
    
    def on_shutdown(self, callback: Callable):
        """Register shutdown callback"""
        self.callbacks['shutdown'] = callback
    
    async def start_monitoring(self, check_interval: int = 60):
        """Start continuous monitoring"""
        self.is_monitoring = True
        logger.info("Risk monitoring started")
        
        while self.is_monitoring:
            try:
                alerts = self.risk_manager.get_risk_alerts()
                
                for alert in alerts:
                    if 'alert' in self.callbacks:
                        await self.callbacks['alert'](alert)
                    
                    logger.warning(f"[{alert['severity']}] {alert['message']}")
                    
                    # Check if should trigger emergency shutdown
                    if alert['severity'] == 'CRITICAL' and alert['type'] == 'total_loss':
                        if 'shutdown' in self.callbacks:
                            await self.callbacks['shutdown'](alert)
                
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in risk monitoring: {e}")
                await asyncio.sleep(check_interval)
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        logger.info("Risk monitoring stopped")


# Demo usage
async def demo():
    """Demonstrate risk management"""
    logger.info("\n" + "="*60)
    logger.info("Risk Management Demo")
    logger.info("="*60)
    
    limits = RiskLimits(
        max_position_size_pct=0.1,
        max_daily_loss_pct=0.05,
        max_total_loss_pct=0.2,
        max_positions=5,
        max_single_trade_loss=5000
    )
    
    risk_mgr = RiskManager(limits, initial_balance=100000)
    
    logger.info("\n✅ Risk Manager initialized")
    logger.info(f"Max position size: {limits.max_position_size_pct:.1%}")
    logger.info(f"Max daily loss: {limits.max_daily_loss_pct:.1%}")
    logger.info(f"Max positions: {limits.max_positions}")
    
    # Test trade approval
    logger.info("\n📊 Testing trade approval...")
    
    trade1 = {
        'symbol': 'BTC/USDT',
        'quantity': 0.5,
        'price': 42000,
        'estimated_loss': 2000
    }
    
    allowed, reason = risk_mgr.can_place_trade(trade1)
    logger.info(f"Trade 1: {'✅ ALLOWED' if allowed else f'❌ REJECTED - {reason}'}")
    
    trade2 = {
        'symbol': 'ETH/USDT',
        'quantity': 500,  # Too large
        'price': 2500,
        'estimated_loss': 1000
    }
    
    allowed, reason = risk_mgr.can_place_trade(trade2)
    logger.info(f"Trade 2: {'✅ ALLOWED' if allowed else f'❌ REJECTED - {reason}'}")
    
    # Register some positions
    logger.info("\n💼 Registering positions...")
    risk_mgr.register_position('BTC/USDT', 0.5, 42000)
    risk_mgr.register_position('ETH/USDT', 5.0, 2500)
    
    logger.info("\n📈 Portfolio Risk Summary:")
    metrics = risk_mgr.get_portfolio_risk()
    for key, value in metrics.items():
        logger.info(f"  {key}: {value}")
    
    # Simulate losses
    logger.info("\n📉 Simulating losses...")
    risk_mgr.update_balance(92000)  # 8% loss
    risk_mgr.update_position_price('BTC/USDT', 40000)
    
    logger.info("\n📈 Updated Portfolio Risk:")
    metrics = risk_mgr.get_portfolio_risk()
    for key, value in metrics.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n⚠️  Risk Alerts:")
    alerts = risk_mgr.get_risk_alerts()
    if alerts:
        for alert in alerts:
            logger.warning(f"  [{alert['severity']}] {alert['message']}")
    else:
        logger.info("  No active alerts")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(demo())
