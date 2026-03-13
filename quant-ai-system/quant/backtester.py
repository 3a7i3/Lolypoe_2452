"""
Backtester
Advanced backtesting engine with walk-forward and Monte Carlo analysis
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class BacktestResult:
    """Backtesting result"""
    total_return: float
    annual_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    num_trades: int
    trades: List[Dict[str, Any]]


@dataclass
class WalkForwardResult:
    """Walk-forward testing result"""
    in_sample_metrics: Dict[str, float]
    out_of_sample_metrics: Dict[str, float]
    degradation: float  # OOS vs IS performance


class Backtester:
    """Advanced backtesting engine"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.results = []
    
    def backtest_strategy(self, prices: List[float], signals: List[Dict[str, Any]],
                         commission: float = 0.001, slippage: float = 0.0001) -> BacktestResult:
        """
        Backtest strategy on historical data
        Args:
            prices: Historical price data
            signals: List of trade signals {'pos': index, 'action': 'BUY'|'SELL'}
            commission: Commission rate per trade
            slippage: Slippage rate per trade
        Returns:
            BacktestResult
        """
        trades = []
        equity_curve = [self.initial_capital]
        position = None
        position_shares = 0
        
        for i, signal in enumerate(signals):
            if i >= len(prices):
                break
            
            price = prices[i]
            price_with_slip = price * (1 + slippage if signal.get('action') == 'BUY' else 1 - slippage)
            
            if signal.get('action') == 'BUY' and position is None:
                # Open position
                shares = (equity_curve[-1] * 0.95) / price_with_slip / (1 + commission)
                position = {
                    'entry_price': price,
                    'entry_index': i,
                    'shares': shares
                }
                position_shares = shares
            
            elif signal.get('action') == 'SELL' and position is not None:
                # Close position
                exit_price = price * (1 - slippage)
                exit_value = position_shares * exit_price * (1 - commission)
                entry_value = position_shares * position['entry_price'] * (1 + commission)
                
                pnl = exit_value - entry_value
                pnl_pct = (exit_value - entry_value) / entry_value
                
                trades.append({
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'shares': position_shares,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'entry_index': position['entry_index'],
                    'exit_index': i
                })
                
                # Update equity
                current_equity = equity_curve[-1] + pnl
                equity_curve.append(current_equity)
                
                position = None
                position_shares = 0
        
        # Calculate metrics
        metrics = self._calculate_metrics(equity_curve, trades)
        
        result = BacktestResult(
            total_return=metrics['total_return'],
            annual_return=metrics['annual_return'],
            sharpe_ratio=metrics['sharpe_ratio'],
            sortino_ratio=metrics['sortino_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            profit_factor=metrics['profit_factor'],
            num_trades=len(trades),
            trades=trades
        )
        
        self.results.append(result)
        return result
    
    def _calculate_metrics(self, equity_curve: List[float],
                          trades: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate backtest metrics"""
        equity_array = np.array(equity_curve)
        
        # Returns
        total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital
        annual_return = total_return / 1  # Assuming 1 year (simplified)
        
        # Sharpe ratio
        returns = np.diff(equity_array) / equity_array[:-1]
        sharpe = np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        sortino = np.mean(returns) / (np.std(downside_returns) + 1e-6) * np.sqrt(252)
        
        # Max drawdown
        running_max = np.maximum.accumulate(equity_array)
        drawdowns = (equity_array - running_max) / running_max
        max_dd = np.min(drawdowns)
        
        # Win rate
        if trades:
            wins = sum(1 for t in trades if t['pnl'] > 0)
            win_rate = wins / len(trades)
        else:
            win_rate = 0
        
        # Profit factor
        gross_profit = sum(max(0, t['pnl']) for t in trades)
        gross_loss = sum(abs(min(0, t['pnl'])) for t in trades)
        profit_factor = gross_profit / (gross_loss + 1e-6)
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }
    
    def walk_forward_test(self, prices: List[float], signals: List[Dict[str, Any]],
                         in_sample_size: int = 0.6, out_sample_size: int = 0.2) -> WalkForwardResult:
        """
        Walk-forward test
        Args:
            prices: Historical prices
            signals: Trade signals
            in_sample_size: Proportion for training
            out_sample_size: Proportion for testing
        """
        total_size = len(prices)
        in_size = int(total_size * in_sample_size)
        out_size = int(total_size * out_sample_size)
        
        # In-sample test
        is_result = self.backtest_strategy(
            prices[:in_size],
            [s for s in signals if s.get('index', 0) < in_size]
        )
        
        # Out-of-sample test
        oos_result = self.backtest_strategy(
            prices[in_size:in_size + out_size],
            [s for s in signals if in_size <= s.get('index', 0) < in_size + out_size]
        )
        
        # Calculate degradation
        is_return = is_result.total_return
        oos_return = oos_result.total_return
        degradation = (is_return - oos_return) / (abs(is_return) + 1e-6)
        
        return WalkForwardResult(
            in_sample_metrics={
                'return': is_result.total_return,
                'sharpe': is_result.sharpe_ratio
            },
            out_of_sample_metrics={
                'return': oos_result.total_return,
                'sharpe': oos_result.sharpe_ratio
            },
            degradation=degradation
        )
    
    def monte_carlo_test(self, prices: List[float], num_simulations: int = 100,
                        randomization_factor: float = 0.1) -> List[BacktestResult]:
        """
        Monte Carlo test with price randomization
        Args:
            prices: Historical prices
            num_simulations: Number of simulations
            randomization_factor: Amount of randomization
        """
        results = []
        
        for _ in range(num_simulations):
            # Add random noise
            random_returns = np.random.normal(0, randomization_factor, len(prices))
            perturbed_prices = prices * (1 + random_returns)
            
            # Generate simple buy/sell signals
            signals = []
            for i in range(1, len(perturbed_prices)):
                if perturbed_prices[i] > perturbed_prices[i-1]:
                    signals.append({'index': i, 'action': 'BUY'})
                else:
                    signals.append({'index': i, 'action': 'SELL'})
            
            # Run backtest
            result = self.backtest_strategy(perturbed_prices, signals)
            results.append(result)
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all backtests"""
        if not self.results:
            return {}
        
        returns = [r.total_return for r in self.results]
        sharpes = [r.sharpe_ratio for r in self.results]
        
        return {
            'num_backtests': len(self.results),
            'avg_return': np.mean(returns),
            'avg_sharpe': np.mean(sharpes),
            'best_return': np.max(returns),
            'worst_return': np.min(returns),
            'win_rate': np.mean([r.win_rate for r in self.results])
        }


# Convenience functions
_backtester = None


def initialize_backtester(initial_capital: float = 100000) -> Backtester:
    """Initialize backtester"""
    global _backtester
    _backtester = Backtester(initial_capital)
    return _backtester


def get_backtester() -> Backtester:
    """Get backtester"""
    global _backtester
    if _backtester is None:
        _backtester = Backtester()
    return _backtester


def run_backtest(prices: List[float], signals: List[Dict[str, Any]]) -> BacktestResult:
    """Run single backtest"""
    return get_backtester().backtest_strategy(prices, signals)
