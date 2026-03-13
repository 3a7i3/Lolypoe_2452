"""
Execution Engine - Smart order execution and trade management
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import config

logger = logging.getLogger(__name__)

class ExecutionEngine:
    """Smart order execution"""
    
    def __init__(self):
        self.trades = []
        self.order_ids = {}
        logger.info("✓ Execution Engine initialized")
    
    async def execute(self, symbol: str, action: str, size: float, confidence: float) -> Optional[Dict]:
        """
        Execute trade with smart order routing
        Returns: execution result
        """
        try:
            # Validate inputs
            if size <= 0 or confidence <= 0:
                logger.warning(f"Invalid execution parameters: {symbol} {action} {size} {confidence}")
                return None
            
            # Check minimum order size
            if size * 100 < config.MIN_ORDER_NOTIONAL:  # Assume price ~100
                logger.debug(f"Order size too small: {symbol}")
                return None
            
            # Select order type
            order_type = await self._select_order_type(symbol, size)
            
            # Execute order
            result = await self._send_order(symbol, action, size, order_type, confidence)
            
            if result:
                self.trades.append(result)
                logger.info(f"✓ Trade executed: {symbol} {action} {size} @ {result.get('price')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return None
    
    async def _select_order_type(self, symbol: str, size: float) -> str:
        """Select order type (limit/market)"""
        try:
            # Use limit orders for better pricing
            if config.ORDER_TYPE == 'limit':
                return 'limit'
            else:
                return 'market'
        except Exception as e:
            logger.debug(f"Order type selection error: {e}")
            return 'market'
    
    async def _send_order(self, symbol: str, action: str, size: float, 
                          order_type: str, confidence: float) -> Optional[Dict]:
        """Send order to exchange"""
        try:
            # Simulate order execution
            price = 100.0  # Placeholder
            slippage = config.EXECUTION_SLIPPAGE
            
            if action == 'BUY':
                execution_price = price * (1 + slippage)
            else:
                execution_price = price * (1 - slippage)
            
            commission = size * execution_price * 0.001  # 0.1% commission
            
            trade = {
                'id': len(self.trades) + 1,
                'symbol': symbol,
                'action': action,
                'quantity': size,
                'order_type': order_type,
                'price': execution_price,
                'commission': commission,
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'status': 'executed'
            }
            
            return trade
            
        except Exception as e:
            logger.error(f"Order send error: {e}")
            return None
    
    async def cancel_order(self, order_id: int) -> bool:
        """Cancel open order"""
        try:
            if order_id in self.order_ids:
                del self.order_ids[order_id]
                logger.info(f"Order cancelled: {order_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return False
    
    def get_trade_history(self, limit: int = 100) -> list:
        """Get recent trade history"""
        return self.trades[-limit:]
    
    def get_pending_orders(self) -> Dict:
        """Get pending orders"""
        return self.order_ids
