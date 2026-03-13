"""
Sharpe Optimizer - Maximum Risk-Adjusted Returns Portfolio
Optimizes for highest Sharpe ratio (risk per unit of return)
"""

import logging
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import minimize

import config

logger = logging.getLogger(__name__)

class SharpeOptimizer:
    """Portfolio optimization targeting maximum Sharpe ratio"""
    
    def __init__(self):
        self.opt_config = config.OPTIMIZATION_METHODS_PARAMS.get('sharpe_maximization', {})
        self.min_position = self.opt_config.get('min_position', 0.00)
        self.max_position = self.opt_config.get('max_position', 0.20)
        self.risk_free_rate = self.opt_config.get('risk_free_rate', 0.02)  # Annual
        self.lookback_period = self.opt_config.get('lookback_period', 252)
        self.target_volatility = self.opt_config.get('target_volatility', 0.15)
        self.diversification_penalty = self.opt_config.get('diversification_penalty', 0.01)
        
        self.optimization_history = []
        self.efficient_frontier = []
        
        logger.info(f"✓ Sharpe Optimizer initialized (target_vol: {self.target_volatility:.1%})")
    
    def optimize_positions(self, returns_df: pd.DataFrame,
                          expected_returns: Dict[str, float] = None) -> Dict[str, float]:
        """
        Calculate positions that maximize Sharpe ratio
        
        Args:
            returns_df: Historical returns for each asset
            expected_returns: Optional forward-looking expected returns
        
        Returns:
            {symbol: position_size} dictionary
        """
        try:
            symbols = list(returns_df.columns)
            n_assets = len(symbols)
            
            if n_assets == 0:
                return {}
            
            # Calculate expected returns
            if expected_returns is None:
                expected_returns = self._calculate_expected_returns(returns_df, symbols)
            else:
                # Validate provided returns
                expected_returns = {s: expected_returns.get(s, 0.0) for s in symbols}
            
            # Calculate covariance matrix
            returns_clean = returns_df[symbols].dropna().tail(self.lookback_period)
            cov_matrix = returns_clean.cov().values
            corr_matrix = returns_clean.corr().values
            
            # Initial guess: equal weight
            x0 = np.array([1.0 / n_assets] * n_assets)
            
            # Constraints
            constraints = self._build_constraints(n_assets, sum_to_one=True)
            
            # Bounds
            bounds = tuple((self.min_position, self.max_position) for _ in range(n_assets))
            
            # Optimize
            result = minimize(
                fun=lambda w: self._negative_sharpe_ratio(w, expected_returns, cov_matrix),
                x0=x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                positions = dict(zip(symbols, result.x))
            else:
                logger.warning(f"Optimization failed: {result.message}")
                positions = {symbol: 1.0 / n_assets for symbol in symbols}
            
            # Scale to target volatility
            positions = self._scale_to_target_volatility(
                positions, returns_clean, self.target_volatility
            )
            
            # Store in history
            sharpe_value = -result.fun if result.success else 0
            self.optimization_history.append({
                'timestamp': datetime.now().isoformat(),
                'method': 'sharpe_maximization',
                'sharpe_ratio': float(sharpe_value),
                'positions': positions,
                'expected_returns': expected_returns
            })
            
            logger.info(f"✓ Sharpe-optimal positions: Sharpe={sharpe_value:.3f}")
            
            return positions
            
        except Exception as e:
            logger.error(f"Sharpe optimization error: {e}")
            return {}
    
    def _calculate_expected_returns(self, returns_df: pd.DataFrame,
                                   symbols: List[str]) -> Dict[str, float]:
        """
        Calculate expected returns using historical data
        Uses trailing mean with exponential weighting
        """
        expected = {}
        
        for symbol in symbols:
            symbol_returns = returns_df[symbol].dropna().tail(self.lookback_period)
            
            if len(symbol_returns) == 0:
                expected[symbol] = 0.0
                continue
            
            # Exponential weighting (recent data more important)
            weights = np.exp(np.linspace(0, 1, len(symbol_returns)))
            weights = weights / weights.sum()
            
            exp_return = (symbol_returns.values * weights).sum()
            
            # Annualize if daily data
            exp_return_annual = exp_return * 252
            
            expected[symbol] = exp_return_annual
        
        return expected
    
    def _negative_sharpe_ratio(self, weights: np.ndarray,
                             expected_returns: Dict[str, float],
                             cov_matrix: np.ndarray) -> float:
        """
        Calculate negative Sharpe ratio (for minimization)
        """
        symbols = list(expected_returns.keys())
        returns_array = np.array([expected_returns[s] for s in symbols])
        
        # Portfolio return
        portfolio_return = np.dot(weights, returns_array)
        
        # Portfolio volatility
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        
        # Sharpe ratio
        sharpe = (portfolio_return - self.risk_free_rate) / (portfolio_vol + 1e-8)
        
        # Add diversification penalty (encourage more equal weighting)
        concentration = np.sum(weights ** 2)
        penalty = self.diversification_penalty * concentration
        
        return -(sharpe - penalty)  # Negative for minimization
    
    def _scale_to_target_volatility(self, positions: Dict[str, float],
                                   returns_df: pd.DataFrame,
                                   target_vol: float) -> Dict[str, float]:
        """
        Scale positions to achieve target portfolio volatility
        """
        try:
            symbols = list(positions.keys())
            weights = np.array([positions[s] for s in symbols])
            
            # Calculate current volatility
            cov_matrix = returns_df[symbols].cov().values
            current_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            
            if current_vol > 0:
                scale_factor = target_vol / current_vol
            else:
                scale_factor = 1.0
            
            # Scale positions but keep allocation percentages
            total_allocated = sum(positions.values())
            scale_factor = min(scale_factor, 0.95 / total_allocated) if total_allocated > 0 else 1.0
            
            scaled = {
                symbol: pos * scale_factor
                for symbol, pos in positions.items()
            }
            
            return scaled
            
        except Exception as e:
            logger.debug(f"Volatility scaling error: {e}")
            return positions
    
    @staticmethod
    def _build_constraints(n_assets: int, sum_to_one: bool = True) -> List:
        """Build optimization constraints"""
        constraints = []
        
        if sum_to_one:
            # Weights sum to 1
            constraints.append({
                'type': 'eq',
                'fun': lambda w: np.sum(w) - 1.0
            })
        
        return constraints
    
    def get_efficient_frontier(self, returns_df: pd.DataFrame,
                              n_points: int = 50) -> Dict:
        """
        Generate efficient frontier: return vs risk at different allocation levels
        """
        try:
            symbols = list(returns_df.columns)
            n_assets = len(symbols)
            
            if n_assets < 2:
                return {'error': 'Need at least 2 assets'}
            
            frontier_points = []
            
            # Test different risk targets
            risk_range = np.linspace(0.05, 0.35, n_points)
            
            for target_risk in risk_range:
                temp_target = self.target_volatility
                self.target_volatility = target_risk
                
                positions = self.optimize_positions(returns_df)
                
                # Calculate metrics
                returns_clean = returns_df[symbols].dropna()
                weights = np.array([positions.get(s, 0) for s in symbols])
                
                exp_returns = self._calculate_expected_returns(returns_df, symbols)
                returns_array = np.array([exp_returns[s] for s in symbols])
                port_return = np.dot(weights, returns_array)
                
                cov_matrix = returns_clean.cov().values
                port_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                
                sharpe = (port_return - self.risk_free_rate) / (port_vol + 1e-8)
                
                frontier_points.append({
                    'risk': float(port_vol),
                    'return': float(port_return),
                    'sharpe': float(sharpe),
                    'positions': positions
                })
                
                self.target_volatility = temp_target
            
            self.efficient_frontier = frontier_points
            
            return {
                'frontier': frontier_points,
                'n_points': len(frontier_points)
            }
            
        except Exception as e:
            logger.error(f"Efficient frontier error: {e}")
            return {'error': str(e)}
    
    def get_position_summary(self, positions: Dict[str, float]) -> Dict:
        """Summarize optimized positions"""
        total_allocated = sum(positions.values())
        
        return {
            'total_positions': len(positions),
            'total_allocated': float(total_allocated),
            'cash_buffer': float(1.0 - total_allocated),
            'target_volatility': float(self.target_volatility),
            'risk_free_rate': float(self.risk_free_rate),
            'positions': positions
        }


logger.info("[SHARPE OPTIMIZER] Risk-adjusted return optimizer loaded")
