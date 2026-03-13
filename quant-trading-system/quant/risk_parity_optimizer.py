"""
Risk Parity Portfolio Optimizer - Equal risk contribution from all assets
Allocates positions inversely proportional to volatility
"""

import logging
from typing import Dict, List
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import minimize

import config

logger = logging.getLogger(__name__)

class RiskParityOptimizer:
    """Portfolio optimization using Risk Parity principle"""
    
    def __init__(self):
        self.opt_config = config.OPTIMIZATION_METHODS_PARAMS.get('risk_parity', {})
        self.min_position = self.opt_config.get('min_position', 0.01)
        self.max_position = self.opt_config.get('max_position', 0.15)
        self.lookback_period = self.opt_config.get('lookback_period', 252)
        self.min_correlation = self.opt_config.get('min_correlation', -0.3)
        self.max_correlation = self.opt_config.get('max_correlation', 0.7)
        
        self.optimization_history = []
        self.position_allocations = {}
        
        logger.info(f"✓ Risk Parity Optimizer initialized (lookback: {self.lookback_period})")
    
    def optimize_positions(self, returns_df: pd.DataFrame,
                          volatilities: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate Risk Parity positions (equal risk contribution)
        
        Args:
            returns_df: Historical returns for each asset
            volatilities: Volatility estimates per asset
        
        Returns:
            {symbol: position_size} dictionary
        """
        try:
            symbols = list(returns_df.columns)
            n_assets = len(symbols)
            
            if n_assets == 0:
                return {}
            
            # Calculate volatilities
            vol_series = {}
            for symbol in symbols:
                if symbol in volatilities:
                    vol_series[symbol] = volatilities[symbol]
                else:
                    symbol_returns = returns_df[symbol].dropna().tail(self.lookback_period)
                    vol_series[symbol] = symbol_returns.std()
            
            # Inverse volatility weighting (risk parity concept)
            inv_vols = {}
            for symbol, vol in vol_series.items():
                if vol > 0:
                    inv_vols[symbol] = 1.0 / vol
                else:
                    inv_vols[symbol] = 1.0 / (0.001)  # Fallback
            
            # Normalize to sum to 1
            total_inv_vol = sum(inv_vols.values())
            
            positions = {}
            for symbol in symbols:
                raw_weight = inv_vols[symbol] / total_inv_vol
                
                # Apply min/max constraints
                position = max(self.min_position, min(self.max_position, raw_weight))
                positions[symbol] = position
            
            # Final normalization to portfolio constraints
            positions = self._normalize_positions(positions, n_assets)
            
            # Adjust for correlation (reduce positions for highly correlated pairs)
            if len(returns_df) > 30:
                positions = self._adjust_for_correlation(returns_df, positions)
            
            # Store history
            self.position_allocations[datetime.now().isoformat()] = positions.copy()
            
            self.optimization_history.append({
                'timestamp': datetime.now().isoformat(),
                'method': 'risk_parity',
                'positions': positions,
                'volatilities': vol_series,
                'inverse_weights': {s: inv_vols[s] / total_inv_vol for s in symbols}
            })
            
            logger.info(f"✓ Risk Parity positions optimized: {n_assets} assets")
            
            return positions
            
        except Exception as e:
            logger.error(f"Risk Parity optimization error: {e}")
            return {}
    
    def _normalize_positions(self, positions: Dict[str, float], n_assets: int) -> Dict[str, float]:
        """
        Normalize positions to portfolio constraints
        """
        try:
            total = sum(positions.values())
            
            if total > 1.0:
                scale_factor = 0.95 / total  # Leave 5% cash
                positions = {
                    symbol: pos * scale_factor
                    for symbol, pos in positions.items()
                }
            
            return positions
            
        except Exception as e:
            logger.error(f"Position normalization error: {e}")
            return positions
    
    def _adjust_for_correlation(self, returns_df: pd.DataFrame,
                               positions: Dict[str, float]) -> Dict[str, float]:
        """
        Adjust positions based on correlation matrix
        Reduce positions for highly correlated pairs
        """
        try:
            symbols = list(positions.keys())
            
            if len(symbols) < 2:
                return positions
            
            # Calculate correlation matrix
            corr_matrix = returns_df[symbols].corr()
            
            # Calculate average correlation for each symbol
            adjusted = positions.copy()
            
            for symbol in symbols:
                # Get correlations with other assets
                correlations = corr_matrix[symbol].drop(symbol)
                
                # Calculate average correlation
                avg_corr = correlations.mean()
                
                # Reduce position if highly correlated with portfolio
                if avg_corr > self.max_correlation:
                    reduction = (avg_corr - self.max_correlation) / (1 - self.max_correlation)
                    adjusted[symbol] = positions[symbol] * (1 - reduction * 0.3)
                
                # Increase position if negatively correlated (diversification benefit)
                elif avg_corr < self.min_correlation:
                    boost = (self.min_correlation - avg_corr) / (self.min_correlation + 1)
                    adjusted[symbol] = min(self.max_position, positions[symbol] * (1 + boost * 0.2))
            
            # Renormalize
            total = sum(adjusted.values())
            if total > 1.0:
                adjusted = {
                    symbol: pos * (0.95 / total)
                    for symbol, pos in adjusted.items()
                }
            
            return adjusted
            
        except Exception as e:
            logger.debug(f"Correlation adjustment error: {e}")
            return positions
    
    def get_position_summary(self, positions: Dict[str, float]) -> Dict:
        """Summarize portfolio positions"""
        total_allocated = sum(positions.values())
        cash_buffer = 1.0 - total_allocated
        
        if positions:
            max_pos = max(positions.values())
            min_pos = min(positions.values())
        else:
            max_pos = 0
            min_pos = 0
        
        return {
            'total_positions': len(positions),
            'total_allocated': float(total_allocated),
            'cash_buffer': float(cash_buffer),
            'max_position': float(max_pos),
            'min_position': float(min_pos),
            'avg_position': float(total_allocated / len(positions)) if positions else 0,
            'positions': positions
        }
    
    def get_optimization_history(self) -> List[Dict]:
        """Get history of optimizations"""
        return self.optimization_history[-100:]  # Last 100 optimizations


logger.info("[RISK PARITY OPTIMIZER] Risk-aware allocation optimizer loaded")
