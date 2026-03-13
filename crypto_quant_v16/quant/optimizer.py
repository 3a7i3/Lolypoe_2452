"""
Optimizer – Multi-objective portfolio optimization
Uses Monte Carlo and Sharpe ratio optimization
"""

import numpy as np
import pandas as pd
import logging
from typing import Any, Dict, List, cast

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """Optimize portfolio allocation using multiple methods"""

    def __init__(self):
        """Initialize optimizer"""
        self.iterations = 0

    def optimize_sharpe(self, returns: np.ndarray, weights: np.ndarray) -> float:
        """Calculate portfolio Sharpe ratio"""
        portfolio_return = np.sum(returns * weights)
        portfolio_std = np.sqrt(np.dot(weights, np.dot(np.cov(returns.T), weights)))
        
        sharpe = portfolio_return / portfolio_std if portfolio_std > 0 else 0
        return sharpe * np.sqrt(252)  # Annualized

    def optimize_min_variance(self, returns: np.ndarray, n_assets: int) -> np.ndarray:
        """Find minimum variance portfolio"""
        cov_matrix = np.cov(returns.T)
        ones = np.ones(n_assets)
        inv_cov = np.linalg.inv(cov_matrix)
        
        weights = np.dot(inv_cov, ones)
        weights /= np.sum(weights)
        
        return weights

    def optimize_max_sharpe(self, returns: np.ndarray, num_iterations: int = 10000) -> Dict[str, Any]:
        """Find maximum Sharpe ratio portfolio using random search"""
        n_assets = returns.shape[1]
        best_sharpe = -np.inf
        best_weights: np.ndarray | None = None

        for _ in range(num_iterations):
            weights = np.random.dirichlet(np.ones(n_assets))
            sharpe = self.optimize_sharpe(returns, weights)
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = weights

        if best_weights is None:
            best_weights = np.ones(n_assets) / n_assets
        weights = cast(np.ndarray, best_weights)

        return {
            'weights': weights,
            'sharpe_ratio': best_sharpe,
            'portfolio_return': np.sum(returns.mean(axis=0) * weights) * 252,
            'portfolio_std': np.sqrt(np.dot(weights, np.dot(np.cov(returns.T), weights))) * np.sqrt(252)
        }

    def efficient_frontier(self, returns: np.ndarray, num_portfolios: int = 5000) -> pd.DataFrame:
        """Generate efficient frontier"""
        results = []
        n_assets = returns.shape[1]

        for _ in range(num_portfolios):
            weights = np.random.dirichlet(np.ones(n_assets))
            
            portfolio_return = np.sum(returns.mean(axis=0) * weights) * 252
            portfolio_std = np.sqrt(np.dot(weights, np.dot(np.cov(returns.T), weights))) * np.sqrt(252)
            sharpe = portfolio_return / portfolio_std if portfolio_std > 0 else 0
            
            results.append({
                'return': portfolio_return,
                'std': portfolio_std,
                'sharpe': sharpe,
                'weights': weights
            })

        return pd.DataFrame(results)

    def kelly_allocation(self, win_rate: float, avg_win: float, 
                        avg_loss: float) -> float:
        """Kelly Criterion for position sizing"""
        if avg_loss == 0:
            return 0
        
        kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_loss
        kelly = np.clip(kelly, 0, 0.25)  # Cap at 25%
        
        return kelly

    def rebalance_portfolio(self, current_allocation: Dict[str, float],
                          target_allocation: Dict[str, float],
                          current_prices: Dict[str, float]) -> List[Dict]:
        """Calculate rebalancing trades"""
        trades = []
        
        for asset, target_pct in target_allocation.items():
            current_pct = current_allocation.get(asset, 0)
            diff = target_pct - current_pct
            
            if abs(diff) > 0.01:  # Only rebalance if diff > 1%
                trades.append({
                    'asset': asset,
                    'action': 'BUY' if diff > 0 else 'SELL',
                    'pct_change': diff,
                    'price': current_prices.get(asset, 0)
                })
        
        logger.info(f"🔄 Rebalancing: {len(trades)} trades recommended")
        return trades

    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate optimization report"""
        return {
            'iterations': self.iterations,
            'status': 'Ready'
        }
