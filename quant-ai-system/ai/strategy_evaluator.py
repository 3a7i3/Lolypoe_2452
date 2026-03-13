"""
Strategy Evaluator
Automatically tests and scores strategies
"""

import numpy as np
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class BacktestResult:
    """Backtest result"""
    strategy_id: str
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trades: int
    score: float


class StrategyEvaluator:
    """AI Strategy Evaluator"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
    
    def evaluate_strategy(self, strategy: Dict[str, Any], market_data: Dict[str, Any]) -> BacktestResult:
        """Evaluate a strategy on market data"""
        
        # Simulate trades based on strategy
        trades = self._simulate_trades(strategy, market_data)
        
        if not trades:
            return BacktestResult(
                strategy_id=strategy.get('id', 'UNKNOWN'),
                total_return=-0.5,
                sharpe_ratio=-10,
                sortino_ratio=-10,
                max_drawdown=1.0,
                win_rate=0.0,
                profit_factor=0.0,
                trades=0,
                score=-100
            )
        
        # Calculate metrics
        returns = np.array([t['return'] for t in trades])
        
        total_return = np.sum(returns) / self.initial_capital
        sharpe_ratio = self._calculate_sharpe(returns)
        sortino_ratio = self._calculate_sortino(returns)
        max_drawdown = self._calculate_max_drawdown(returns)
        win_rate = np.mean(returns > 0)
        profit_factor = self._calculate_profit_factor(returns)
        
        # Calculate composite score
        score = self._calculate_score(
            total_return, sharpe_ratio, win_rate, max_drawdown, profit_factor
        )
        
        return BacktestResult(
            strategy_id=strategy.get('id', 'UNKNOWN'),
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            trades=len(trades),
            score=score
        )
    
    def evaluate_population(self, strategies: List[Dict[str, Any]], market_data: Dict[str, Any]) -> List[BacktestResult]:
        """Evaluate population of strategies"""
        results = []
        for strategy in strategies:
            result = self.evaluate_strategy(strategy, market_data)
            results.append(result)
        return sorted(results, key=lambda x: x.score, reverse=True)
    
    def _simulate_trades(self, strategy: Dict[str, Any], market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate trades based on strategy"""
        trades = []
        
        # Simulate random trades for demo
        num_trades = np.random.randint(10, 100)
        
        for _ in range(num_trades):
            # Random return between -5% and +10%
            ret = np.random.normal(0.01, 0.02)
            trades.append({'return': ret})
        
        return trades
    
    def _calculate_sharpe(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if returns.std() == 0:
            return 0
        return (returns.mean() - risk_free_rate) / returns.std()
    
    def _calculate_sortino(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio"""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return 0
        downside_std = downside_returns.std()
        if downside_std == 0:
            return 0
        return (returns.mean() - risk_free_rate) / downside_std
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumprod(1 + returns) - 1
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / (1 + running_max)
        return np.min(drawdown)
    
    def _calculate_profit_factor(self, returns: np.ndarray) -> float:
        """Calculate profit factor"""
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        
        if losses == 0:
            return 1.0 if gains > 0 else 0.0
        
        return gains / losses
    
    def _calculate_score(self, total_return: float, sharpe: float, win_rate: float, 
                        max_dd: float, pf: float) -> float:
        """Calculate composite score"""
        # Weighted combination of metrics
        score = (
            total_return * 20 +          # Weight: 20
            sharpe * 5 +                  # Weight: 5
            win_rate * 10 +               # Weight: 10
            (1 - abs(max_dd)) * 15 +     # Weight: 15
            min(pf, 5) * 5                # Weight: 5 (capped at 5)
        )
        return score


# Convenience functions
_evaluator = StrategyEvaluator()

def evaluate_strategy(strategy: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single strategy"""
    result = _evaluator.evaluate_strategy(strategy, market_data)
    return {
        'strategy_id': result.strategy_id,
        'total_return': result.total_return,
        'sharpe_ratio': result.sharpe_ratio,
        'sortino_ratio': result.sortino_ratio,
        'max_drawdown': result.max_drawdown,
        'win_rate': result.win_rate,
        'profit_factor': result.profit_factor,
        'trades': result.trades,
        'score': result.score
    }


def evaluate_population(strategies: List[Dict[str, Any]], market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluate population of strategies"""
    results = _evaluator.evaluate_population(strategies, market_data)
    return [
        {
            'strategy_id': r.strategy_id,
            'total_return': r.total_return,
            'sharpe_ratio': r.sharpe_ratio,
            'max_drawdown': r.max_drawdown,
            'win_rate': r.win_rate,
            'score': r.score
        }
        for r in results
    ]
