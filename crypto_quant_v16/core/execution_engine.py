"""
Execution Engine – Order placement and management
Market/limit orders, stop-loss, position tracking
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Handle order execution and position management"""

    def __init__(self, exchange_manager, mode: str = 'paper'):
        """Initialize execution engine"""
        self.em = exchange_manager
        self.mode = mode  # 'paper' or 'live'
        self.orders = {}
        self.trades = []

    async def create_order(self, symbol: str, side: str, amount: float, 
                          order_type: str = 'market', price: float = None) -> Dict:
        """Create and execute order"""
        
        if self.mode == 'paper':
            # Paper trading simulation
            order = {
                'id': len(self.orders),
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price or 0,
                'type': order_type,
                'status': 'closed' if order_type == 'market' else 'pending',
                'timestamp': datetime.now().isoformat()
            }
            self.orders[order['id']] = order
            logger.info(f"📄 Paper order: {side} {amount} {symbol}")
            return order
        else:
            # Live trading
            try:
                order = await self.em.place_order(symbol, order_type, side, amount, price)
                logger.info(f"✅ Live order placed: {order}")
                self.orders[order['id']] = order
                return order
            except Exception as e:
                logger.error(f"❌ Order failed: {e}")
                return None

    async def set_stop_loss(self, symbol: str, entry_price: float, 
                           stop_loss_pct: float = 0.05) -> Dict:
        """Create stop-loss order"""
        stop_price = entry_price * (1 - stop_loss_pct)
        
        sl_order = {
            'symbol': symbol,
            'type': 'stop_loss',
            'entry_price': entry_price,
            'stop_price': stop_price,
            'stop_loss_pct': stop_loss_pct,
            'status': 'active'
        }
        
        logger.info(f"🛑 Stop-loss set: {symbol} @ {stop_price}")
        return sl_order

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel pending order"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order['status'] == 'pending':
                if self.mode == 'paper':
                    order['status'] = 'cancelled'
                else:
                    await self.em.cancel_order(order_id, symbol)
                logger.info(f"❌ Order cancelled: {order_id}")
                return True
        return False

    def get_order_history(self) -> List[Dict]:
        """Get all orders"""
        return list(self.orders.values())

    async def check_fill_conditions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """Check and execute pending orders based on price"""
        filled = []
        
        for order_id, order in self.orders.items():
            if order['status'] == 'pending' and order['symbol'] in current_prices:
                current = current_prices[order['symbol']]
                
                if order['type'] == 'limit' and order['side'] == 'buy':
                    if current <= order['price']:
                        order['status'] = 'filled'
                        order['fill_price'] = current
                        filled.append(order)
                        
                elif order['type'] == 'limit' and order['side'] == 'sell':
                    if current >= order['price']:
                        order['status'] = 'filled'
                        order['fill_price'] = current
                        filled.append(order)

        return filled

    def get_order_stats(self) -> Dict[str, Any]:
        """Get order statistics"""
        total_orders = len(self.orders)
        filled = sum(1 for o in self.orders.values() if o['status'] == 'filled')
        pending = sum(1 for o in self.orders.values() if o['status'] == 'pending')
        cancelled = sum(1 for o in self.orders.values() if o['status'] == 'cancelled')
        
        return {
            'total_orders': total_orders,
            'filled': filled,
            'pending': pending,
            'cancelled': cancelled,
            'fill_rate': (filled / total_orders * 100) if total_orders > 0 else 0
        }
