"""
Execution Engine
Handles order placement and trade execution
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime


class OrderType(Enum):
    """Order types"""
    MARKET = 'market'
    LIMIT = 'limit'
    STOP = 'stop'


class OrderSide(Enum):
    """Order side: BUY or SELL"""
    BUY = 'buy'
    SELL = 'sell'


class OrderStatus(Enum):
    """Order status"""
    PENDING = 'pending'
    OPEN = 'open'
    PARTIAL = 'partial'
    CLOSED = 'closed'
    CANCELLED = 'cancelled'
    REJECTED = 'rejected'


@dataclass
class Order:
    """Single order"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float = 0.0  # For limit orders
    stop_price: float = 0.0  # For stop orders
    
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    commission: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: Optional[datetime] = None
    
    # Additional metadata
    strategy_id: str = None
    comment: str = ""


class ExecutionEngine:
    """Executes orders and manages trades"""
    
    def __init__(self, commission_rate: float = 0.001, slippage_percent: float = 0.01):
        """
        Initialize execution engine
        Args:
            commission_rate: Trading commission (0.1%)
            slippage_percent: Expected slippage on large orders (0.01%)
        """
        self.commission_rate = commission_rate
        self.slippage_percent = slippage_percent
        
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.executions: List[Dict[str, Any]] = []
        self.rejected_orders: List[Order] = []
    
    def create_order(self, symbol: str, side: OrderSide, quantity: float,
                    order_type: OrderType = OrderType.MARKET, price: float = 0.0,
                    strategy_id: str = None, comment: str = "") -> Order:
        """Create new order"""
        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            strategy_id=strategy_id,
            comment=comment
        )
        
        return order
    
    def submit_order(self, order: Order, validate: bool = True) -> bool:
        """
        Submit order for execution
        Returns: True if successful
        """
        if validate:
            if not self._validate_order(order):
                self.rejected_orders.append(order)
                order.status = OrderStatus.REJECTED
                return False
        
        order.status = OrderStatus.OPEN
        self.orders[order.order_id] = order
        
        # Simulate immediate market execution
        if order.order_type == OrderType.MARKET:
            self._execute_market_order(order)
        
        return True
    
    def _validate_order(self, order: Order) -> bool:
        """Validate order before submission"""
        # Quantity check
        if order.quantity <= 0:
            return False
        
        # Price check for limit orders
        if order.order_type == OrderType.LIMIT and order.price <= 0:
            return False
        
        # Stop price check
        if order.order_type == OrderType.STOP and order.stop_price <= 0:
            return False
        
        return True
    
    def _execute_market_order(self, order: Order, market_price: float = None):
        """Execute market order immediately"""
        if market_price is None:
            # Use the limit price as market price (for simulation)
            market_price = order.price or 100.0  # Default fallback
        
        # Apply slippage
        if order.side == OrderSide.BUY:
            execution_price = market_price * (1 + self.slippage_percent)
        else:
            execution_price = market_price * (1 - self.slippage_percent)
        
        # Calculate commission
        order_value = order.quantity * execution_price
        commission = order_value * self.commission_rate
        
        # Update order
        order.filled_quantity = order.quantity
        order.average_fill_price = execution_price
        order.commission = commission
        order.status = OrderStatus.CLOSED
        order.execution_time = datetime.now()
        
        # Record execution
        self.executions.append({
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'price': execution_price,
            'commission': commission,
            'timestamp': order.execution_time
        })
    
    def execute_limit_order(self, order: Order, market_price: float) -> bool:
        """
        Execute limit order if market price meets condition
        Returns: True if executed
        """
        if order.status != OrderStatus.OPEN:
            return False
        
        should_execute = False
        
        if order.side == OrderSide.BUY and market_price <= order.price:
            should_execute = True
        elif order.side == OrderSide.SELL and market_price >= order.price:
            should_execute = True
        
        if should_execute:
            self._execute_market_order(order, market_price)
            return True
        
        return False
    
    def execute_stop_order(self, order: Order, market_price: float) -> bool:
        """
        Execute stop order if market price meets condition
        Returns: True if executed
        """
        if order.status != OrderStatus.OPEN:
            return False
        
        should_execute = False
        
        if order.side == OrderSide.BUY and market_price >= order.stop_price:
            should_execute = True
        elif order.side == OrderSide.SELL and market_price <= order.stop_price:
            should_execute = True
        
        if should_execute:
            self._execute_market_order(order, market_price)
            return True
        
        return False
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel open order"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        if order.status in [OrderStatus.CLOSED, OrderStatus.CANCELLED]:
            return False
        
        order.status = OrderStatus.CANCELLED
        
        return True
    
    def update_orders(self, market_prices: Dict[str, float]):
        """Update order execution based on market prices"""
        for order in self.orders.values():
            if order.symbol not in market_prices:
                continue
            
            market_price = market_prices[order.symbol]
            
            if order.order_type == OrderType.LIMIT:
                self.execute_limit_order(order, market_price)
            elif order.order_type == OrderType.STOP:
                self.execute_stop_order(order, market_price)
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        return self.orders.get(order_id)
    
    def get_open_orders(self) -> List[Order]:
        """Get all open orders"""
        return [o for o in self.orders.values() if o.status == OrderStatus.OPEN]
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.executions[-limit:]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        if not self.executions:
            return {}
        
        total_quantity = sum(e['quantity'] for e in self.executions)
        total_commission = sum(e['commission'] for e in self.executions)
        
        buy_orders = [e for e in self.executions if e['side'] == 'buy']
        sell_orders = [e for e in self.executions if e['side'] == 'sell']
        
        return {
            'total_executions': len(self.executions),
            'total_quantity': total_quantity,
            'total_commission': total_commission,
            'avg_commission_per_trade': total_commission / len(self.executions),
            'buy_orders': len(buy_orders),
            'sell_orders': len(sell_orders),
            'open_orders': len(self.get_open_orders()),
            'rejected_orders': len(self.rejected_orders)
        }


# Convenience functions
_engine = None


def initialize_execution_engine(commission_rate: float = 0.001) -> ExecutionEngine:
    """Initialize execution engine"""
    global _engine
    _engine = ExecutionEngine(commission_rate=commission_rate)
    return _engine


def get_execution_engine() -> ExecutionEngine:
    """Get execution engine"""
    global _engine
    if _engine is None:
        _engine = ExecutionEngine()
    return _engine


def create_and_submit_order(symbol: str, side: str, quantity: float,
                           order_type: str = 'market', price: float = 0.0) -> bool:
    """Create and submit order"""
    engine = get_execution_engine()
    
    order = engine.create_order(
        symbol=symbol,
        side=OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL,
        quantity=quantity,
        order_type=OrderType.MARKET if order_type.upper() == 'MARKET' else OrderType.LIMIT,
        price=price
    )
    
    return engine.submit_order(order)
