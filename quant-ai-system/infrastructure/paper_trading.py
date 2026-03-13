"""
Paper Trading Mode
Risk-free backtesting and testing without real funds
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class PaperPosition:
    """Paper trading position"""
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    entry_price: float
    current_price: float
    entry_time: datetime
    pnl: float = 0.0
    pnl_pct: float = 0.0
    
    def update_price(self, current_price: float):
        """Update position with current price"""
        self.current_price = current_price
        
        if self.side == 'buy':
            self.pnl = (current_price - self.entry_price) * self.quantity
            self.pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # sell
            self.pnl = (self.entry_price - current_price) * self.quantity
            self.pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100


@dataclass
class PaperTrade:
    """Completed paper trade"""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    commission: float = 0.0
    
    def close(self, exit_price: float, commission: float = 0.0):
        """Close trade"""
        self.exit_price = exit_price
        self.exit_time = datetime.now()
        self.commission = commission
        
        if self.side == 'buy':
            self.pnl = ((exit_price - self.entry_price) * self.quantity) - commission
            self.pnl_pct = ((exit_price - self.entry_price) / self.entry_price) * 100
        else:  # sell
            self.pnl = ((self.entry_price - exit_price) * self.quantity) - commission
            self.pnl_pct = ((self.entry_price - exit_price) / self.entry_price) * 100


class PaperTradingAccount:
    """Paper trading account"""
    
    def __init__(self, initial_balance: float = 100000.0, commission_rate: float = 0.001):
        """Initialize paper trading account"""
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, PaperPosition] = {}
        self.closed_trades: List[PaperTrade] = []
        self.commission_rate = commission_rate
        self.trades_executed = 0
        self.trades_closed = 0
        
        logger.info(f"Paper Trading Account initialized: ${initial_balance:,.2f}")
    
    def place_buy_order(self, symbol: str, quantity: float, price: float) -> bool:
        """Place buy order (paper trading)"""
        cost = (quantity * price) * (1 + self.commission_rate)
        
        if cost > self.balance:
            logger.warning(f"Insufficient balance for {symbol}: need ${cost:,.2f}, have ${self.balance:,.2f}")
            return False
        
        # Create position
        position = PaperPosition(
            symbol=symbol,
            side='buy',
            quantity=quantity,
            entry_price=price,
            current_price=price,
            entry_time=datetime.now()
        )
        
        self.positions[symbol] = position
        self.balance -= cost
        self.trades_executed += 1
        
        logger.info(f"📈 Buy order: {symbol} {quantity}@${price} (Cost: ${cost:,.2f})")
        
        return True
    
    def place_sell_order(self, symbol: str, quantity: float, price: float) -> bool:
        """Place sell order (paper trading)"""
        if symbol not in self.positions:
            logger.warning(f"No position for {symbol}")
            return False
        
        position = self.positions[symbol]
        
        if position.quantity < quantity:
            logger.warning(f"Insufficient quantity for {symbol}: have {position.quantity}, want {quantity}")
            return False
        
        # Calculate sale proceeds
        proceeds = (quantity * price) * (1 - self.commission_rate)
        commission = quantity * price * self.commission_rate
        
        # Create closed trade
        trade = PaperTrade(
            symbol=symbol,
            side='buy',  # Original buy
            quantity=quantity,
            entry_price=position.entry_price,
            exit_price=price,
            entry_time=position.entry_time,
            exit_time=datetime.now()
        )
        trade.close(price, commission)
        
        self.closed_trades.append(trade)
        self.balance += proceeds
        self.trades_closed += 1
        
        # Update or remove position
        if position.quantity == quantity:
            del self.positions[symbol]
        else:
            position.quantity -= quantity
        
        logger.info(f"📉 Sell order: {symbol} {quantity}@${price} (Proceeds: ${proceeds:,.2f})")
        
        return True
    
    def update_position_prices(self, prices: Dict[str, float]):
        """Update all positions with current prices"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)
    
    def get_account_value(self) -> float:
        """Get total account value"""
        positions_value = sum(
            pos.quantity * pos.current_price 
            for pos in self.positions.values()
        )
        return self.balance + positions_value
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary"""
        account_value = self.get_account_value()
        total_pnl = sum(trade.pnl for trade in self.closed_trades)
        total_pnl_pct = (total_pnl / self.initial_balance) * 100 if self.initial_balance > 0 else 0
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'positions_value': account_value - self.balance,
            'account_value': account_value,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'open_positions': len(self.positions),
            'closed_trades': len(self.closed_trades),
            'trades_executed': self.trades_executed,
            'avg_return': total_pnl / self.trades_closed if self.trades_closed > 0 else 0,
            'win_rate': self._calculate_win_rate(),
        }
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if not self.closed_trades:
            return 0.0
        
        winning = len([t for t in self.closed_trades if t.pnl > 0])
        return (winning / len(self.closed_trades)) * 100
    
    def get_open_positions(self) -> Dict[str, Dict]:
        """Get open positions"""
        return {
            symbol: {
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'pnl': pos.pnl,
                'pnl_pct': pos.pnl_pct,
                'entry_time': pos.entry_time.isoformat()
            }
            for symbol, pos in self.positions.items()
        }
    
    def get_closed_trades(self, limit: int = 100) -> List[Dict]:
        """Get closed trades"""
        return [
            {
                'symbol': trade.symbol,
                'quantity': trade.quantity,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'pnl': trade.pnl,
                'pnl_pct': trade.pnl_pct,
                'commission': trade.commission,
                'entry_time': trade.entry_time.isoformat(),
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None
            }
            for trade in self.closed_trades[-limit:]
        ]
    
    def reset(self):
        """Reset account"""
        self.balance = self.initial_balance
        self.positions.clear()
        self.closed_trades.clear()
        self.trades_executed = 0
        self.trades_closed = 0
        logger.info("Paper trading account reset")


class PaperTradingMode:
    """Paper trading mode for risk-free testing"""
    
    def __init__(self, initial_balance: float = 100000.0):
        self.account = PaperTradingAccount(initial_balance)
        self.is_enabled = True
        
        logger.info("Paper Trading Mode enabled")
    
    async def execute_trade(self, trade_signal: Dict) -> bool:
        """Execute trade in paper mode"""
        if not self.is_enabled:
            logger.warning("Paper trading mode is disabled")
            return False
        
        symbol = trade_signal.get('symbol')
        side = trade_signal.get('side')
        quantity = trade_signal.get('quantity')
        price = trade_signal.get('price')
        
        if side == 'buy':
            return self.account.place_buy_order(symbol, quantity, price)
        elif side == 'sell':
            return self.account.place_sell_order(symbol, quantity, price)
        else:
            logger.error(f"Unknown side: {side}")
            return False
    
    async def close_position(self, symbol: str, exit_price: float) -> bool:
        """Close position in paper mode"""
        if symbol not in self.account.positions:
            logger.warning(f"No position to close for {symbol}")
            return False
        
        position = self.account.positions[symbol]
        return self.account.place_sell_order(symbol, position.quantity, exit_price)
    
    def get_performance(self) -> Dict[str, Any]:
        """Get paper trading performance"""
        summary = self.account.get_account_summary()
        
        return {
            'status': 'active' if self.is_enabled else 'disabled',
            'account_summary': summary,
            'open_positions': self.account.get_open_positions(),
            'recent_trades': self.account.get_closed_trades(limit=10)
        }
    
    def disable(self):
        """Disable paper trading (for real trading)"""
        self.is_enabled = False
        logger.info("Paper trading mode disabled")
    
    def enable(self):
        """Enable paper trading"""
        self.is_enabled = True
        logger.info("Paper trading mode enabled")


# Demo usage
async def demo():
    """Demonstrate paper trading"""
    logger.info("\n" + "="*60)
    logger.info("Paper Trading Mode Demo")
    logger.info("="*60)
    
    paper = PaperTradingMode(initial_balance=100000)
    
    logger.info("\n💼 Account Summary (Initial):")
    summary = paper.account.get_account_summary()
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n📈 Placing trades...")
    
    # Buy BTC
    await paper.execute_trade({
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'quantity': 0.5,
        'price': 42000
    })
    
    # Buy ETH
    await paper.execute_trade({
        'symbol': 'ETH/USDT',
        'side': 'buy',
        'quantity': 5.0,
        'price': 2500
    })
    
    logger.info("\n💰 Account after trades:")
    summary = paper.account.get_account_summary()
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n📊 Open Positions:")
    positions = paper.account.get_open_positions()
    for symbol, pos in positions.items():
        logger.info(f"  {symbol}: {pos['quantity']} @ {pos['entry_price']} (Current: {pos['current_price']})")
    
    # Simulate price changes
    logger.info("\n📉 Price update (+5% for BTC, +3% for ETH)...")
    paper.account.update_position_prices({
        'BTC/USDT': 42000 * 1.05,
        'ETH/USDT': 2500 * 1.03
    })
    
    logger.info("\n📊 Open Positions (after price update):")
    positions = paper.account.get_open_positions()
    for symbol, pos in positions.items():
        logger.info(f"  {symbol}: PnL={pos['pnl']:,.2f} ({pos['pnl_pct']:.2f}%)")
    
    # Close BTC position
    logger.info("\n📉 Closing BTC position...")
    await paper.close_position('BTC/USDT', 42000 * 1.05)
    
    logger.info("\n✅ Closed Trades:")
    trades = paper.account.get_closed_trades()
    for trade in trades:
        logger.info(f"  {trade['symbol']}: {trade['quantity']} units - PnL: ${trade['pnl']:,.2f}")
    
    logger.info("\n💼 Final Account Summary:")
    summary = paper.account.get_account_summary()
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(demo())
