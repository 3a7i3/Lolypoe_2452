"""
Portfolio Manager
Dynamic position sizing and rebalancing
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, field
import numpy as np


@dataclass
class Position:
    """Single position in portfolio"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    status: str  # 'OPEN', 'CLOSED', 'PENDING'
    strategy_id: str = None
    entry_time: float = None
    unrealized_pnl: float = field(init=False)
    
    def __post_init__(self):
        self.unrealized_pnl = (self.current_price - self.entry_price) * self.quantity


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    total_value: float
    available_cash: float
    used_cash: float
    portfolio_return: float
    total_positions: int
    winning_positions: int
    losing_positions: int
    avg_position_size: float
    concentration: float  # Highest position as % of portfolio
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0


class PortfolioManager:
    """Manages portfolio positions and allocation"""
    
    def __init__(self, initial_capital: float = 100000, max_positions: int = 20,
                 max_position_size: float = 0.10, max_drawdown: float = 0.25):
        """
        Initialize portfolio manager
        Args:
            initial_capital: Starting capital
            max_positions: Maximum number of open positions
            max_position_size: Max % of portfolio per position
            max_drawdown: Maximum allowed drawdown before halt
        """
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.max_positions = max_positions
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        
        self.positions: Dict[str, Position] = {}
        self.position_history: List[Position] = []
        self.equity_curve = [initial_capital]
        self.portfolio_history = []
    
    def calculate_kelly_position_size(self, win_rate: float, profit_factor: float,
                                      signal_strength: float = 1.0) -> float:
        """
        Calculate position size using Kelly Criterion
        Args:
            win_rate: Historical win rate
            profit_factor: Profit factor (wins/losses)
            signal_strength: Signal confidence (0-1)
        Returns:
            Position size as % of portfolio
        """
        if win_rate <= 0 or profit_factor <= 0:
            return 0.01  # Minimum 1%
        
        # Kelly formula: (bp - q) / b
        # b = profit/loss ratio, p = win rate, q = 1 - p
        win_loss_ratio = profit_factor
        
        kelly_percent = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Apply safety factor (use half Kelly)
        kelly_percent = kelly_percent * 0.5 * signal_strength
        
        # Bounds
        kelly_percent = np.clip(kelly_percent, 0.01, self.max_position_size)
        
        return kelly_percent
    
    def open_position(self, symbol: str, quantity: float, entry_price: float,
                     strategy_id: str = None, entry_time: float = None) -> bool:
        """
        Open new position
        Returns: True if successful, False otherwise
        """
        position_value = quantity * entry_price
        
        # Check constraints
        if position_value > self.current_cash:
            print(f"Insufficient cash: need {position_value}, have {self.current_cash}")
            return False
        
        if len(self.positions) >= self.max_positions:
            print(f"Max positions reached: {self.max_positions}")
            return False
        
        portfolio_value = self.get_portfolio_value()
        position_percent = position_value / portfolio_value
        
        if position_percent > self.max_position_size:
            print(f"Position too large: {position_percent:.2%} > {self.max_position_size:.2%}")
            return False
        
        # Create position
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            status='OPEN',
            strategy_id=strategy_id,
            entry_time=entry_time
        )
        
        self.positions[symbol] = position
        self.current_cash -= position_value
        
        return True
    
    def close_position(self, symbol: str, exit_price: float) -> bool:
        """Close existing position"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        position.current_price = exit_price
        position.status = 'CLOSED'
        
        # Return cash
        self.current_cash += position.quantity * exit_price
        
        # Move to history
        self.position_history.append(position)
        del self.positions[symbol]
        
        return True
    
    def update_position_prices(self, prices: Dict[str, float]):
        """Update market prices for all positions"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price
                self.positions[symbol].unrealized_pnl = \
                    (price - self.positions[symbol].entry_price) * self.positions[symbol].quantity
    
    def rebalance_positions(self, target_allocations: Dict[str, float]):
        """
        Rebalance portfolio to target allocations
        Args:
            target_allocations: Dict of symbol -> target % allocation
        """
        portfolio_value = self.get_portfolio_value()
        
        for symbol, target_percent in target_allocations.items():
            target_value = portfolio_value * target_percent
            
            if symbol in self.positions:
                current_value = self.positions[symbol].quantity * self.positions[symbol].current_price
                
                if current_value < target_value * 0.9:
                    # Buy more
                    additional_value = target_value - current_value
                    additional_quantity = additional_value / self.positions[symbol].current_price
                    self.positions[symbol].quantity += additional_quantity
                    self.current_cash -= additional_value
                
                elif current_value > target_value * 1.1:
                    # Sell some
                    excess_value = current_value - target_value
                    sell_quantity = excess_value / self.positions[symbol].current_price
                    self.positions[symbol].quantity -= sell_quantity
                    self.current_cash += excess_value
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        positions_value = sum(
            pos.quantity * pos.current_price
            for pos in self.positions.values()
        )
        return self.current_cash + positions_value
    
    def get_portfolio_return(self) -> float:
        """Get portfolio return %"""
        portfolio_value = self.get_portfolio_value()
        return (portfolio_value - self.initial_capital) / self.initial_capital
    
    def get_metrics(self) -> PortfolioMetrics:
        """Get portfolio metrics"""
        portfolio_value = self.get_portfolio_value()
        positions_value = portfolio_value - self.current_cash
        
        winning = sum(1 for pos in self.positions.values() if pos.unrealized_pnl > 0)
        losing = sum(1 for pos in self.positions.values() if pos.unrealized_pnl < 0)
        
        position_sizes = [
            (pos.quantity * pos.current_price) / portfolio_value
            for pos in self.positions.values()
        ]
        avg_size = np.mean(position_sizes) if position_sizes else 0
        max_concentration = max(position_sizes) if position_sizes else 0
        
        return PortfolioMetrics(
            total_value=portfolio_value,
            available_cash=self.current_cash,
            used_cash=positions_value,
            portfolio_return=self.get_portfolio_return(),
            total_positions=len(self.positions),
            winning_positions=winning,
            losing_positions=losing,
            avg_position_size=avg_size,
            concentration=max_concentration
        )
    
    def check_max_drawdown(self) -> bool:
        """Check if max drawdown exceeded"""
        if not self.equity_curve:
            return True
        
        peak = max(self.equity_curve)
        current = self.get_portfolio_value()
        drawdown = (peak - current) / peak
        
        return drawdown <= self.max_drawdown
    
    def update_equity_curve(self):
        """Update equity curve with current portfolio value"""
        self.equity_curve.append(self.get_portfolio_value())
        
        # Keep history limit to last 1000 points
        if len(self.equity_curve) > 1000:
            self.equity_curve = self.equity_curve[-1000:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get portfolio status"""
        metrics = self.get_metrics()
        
        return {
            'portfolio_value': metrics.total_value,
            'available_cash': metrics.available_cash,
            'return': f"{metrics.portfolio_return:.2%}",
            'positions': metrics.total_positions,
            'winners': metrics.winning_positions,
            'losers': metrics.losing_positions
        }


# Convenience functions
_portfolio = None


def initialize_portfolio(initial_capital: float = 100000) -> PortfolioManager:
    """Initialize global portfolio manager"""
    global _portfolio
    _portfolio = PortfolioManager(initial_capital)
    return _portfolio


def get_portfolio() -> PortfolioManager:
    """Get global portfolio manager"""
    global _portfolio
    if _portfolio is None:
        _portfolio = PortfolioManager()
    return _portfolio


def get_portfolio_status() -> Dict[str, Any]:
    """Get portfolio status"""
    return get_portfolio().get_status()
