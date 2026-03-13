"""
Kelly Criterion Portfolio Optimizer - Optimal position sizing using Kelly formula
Maximizes long-term wealth growth while controlling drawdown risk
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import minimize

import config

logger = logging.getLogger(__name__)

class KellyCriterionOptimizer:
    """Portfolio optimization using Kelly Criterion formula"""
    
    def __init__(self):
        self.opt_config = config.OPTIMIZATION_METHODS_PARAMS.get('kelly_criterion', {})
        self.kelly_fraction = self.opt_config.get('kelly_fraction', 0.5)  # Half-Kelly for safety
        self.min_position = self.opt_config.get('min_position', 0.01)
        self.max_position = self.opt_config.get('max_position', 0.10)
        self.transaction_cost = self.opt_config.get('transaction_cost', 0.001)
        
        self.optimization_history = []
        self.position_allocations = {}
        
        logger.info(f"✓ Kelly Criterion Optimizer initialized (kelly_fraction: {self.kelly_fraction})")
    
    def optimize_positions(self, returns_df: pd.DataFrame, 
                          sharpe_ratios: Dict[str, float],
                          win_rates: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate optimal position sizes using Kelly Criterion
        
        Args:
            returns_df: Historical returns for each asset
            sharpe_ratios: Sharpe ratio per asset
            win_rates: Historical win rate (0-1) per asset
        
        Returns:
            {symbol: position_size} dictionary
        """
        try:
            positions = {}
            portfolio_turnover = 0.0
            
            for symbol in returns_df.columns:
                if symbol not in win_rates:
                    positions[symbol] = self.min_position
                    continue
                
                # Extract symbol returns
                symbol_returns = returns_df[symbol].dropna()
                
                if len(symbol_returns) < 30:
                    positions[symbol] = self.min_position
                    continue
                
                # Calculate kelly position
                kelly_pos = self._calculate_kelly_position(
                    symbol_returns,
                    win_rates.get(symbol, 0.5),
                    sharpe_ratios.get(symbol, 0.0)
                )
                
                positions[symbol] = kelly_pos
                portfolio_turnover += abs(kelly_pos)
            
            # Normalize to portfolio constraints
            positions = self._normalize_positions(positions)
            
            # Store history
            self.position_allocations[datetime.now().isoformat()] = positions.copy()
            
            self.optimization_history.append({
                'timestamp': datetime.now().isoformat(),
                'method': 'kelly_criterion',
                'positions': positions,
                'portfolio_turnover': portfolio_turnover,
                'kelly_fraction': self.kelly_fraction
            })
            
            logger.info(f"✓ Kelly positions optimized: {len(positions)} assets, "
                       f"turnover={portfolio_turnover:.2%}")
            
            return positions
            
        except Exception as e:
            logger.error(f"Kelly optimization error: {e}")
            return self._uniform_allocation(list(returns_df.columns) if len(returns_df.columns) > 0 else [])
    
    def _calculate_kelly_position(self, returns: pd.Series, win_rate: float,
                                 sharpe_ratio: float) -> float:
        """
        Calculate Kelly-optimal position size
        
        Kelly % = (win_rate * avg_win - (1-win_rate) * avg_loss) / avg_win
        
        Args:
            returns: Historical returns for asset
            win_rate: Historical winning trade percentage (0-1)
            sharpe_ratio: Sharpe ratio for position scaling
        
        Returns:
            Optimal position size (as fraction of capital)
        """
        try:
            # Calculate average win/loss
            positive_returns = returns[returns > 0]
            negative_returns = returns[returns < 0]
            
            avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0.001
            avg_loss = abs(negative_returns.mean()) if len(negative_returns) > 0 else 0.001
            
            # Ensure we don't divide by zero
            if avg_win <= 0:
                avg_win = 0.001
            
            # Standard Kelly formula
            if win_rate >= 0 and win_rate <= 1:
                kelly_pct = ((win_rate * avg_win) - ((1 - win_rate) * avg_loss)) / avg_win
            else:
                kelly_pct = 0
            
            # Apply half-kelly safety adjustment
            kelly_adjusted = kelly_pct * self.kelly_fraction
            
            # Scale by Sharpe ratio quality (higher Sharpe = more confidence)
            sharpe_scalar = max(0.5, min(2.0, 1.0 + (sharpe_ratio * 0.3)))
            kelly_final = kelly_adjusted * sharpe_scalar
            
            # Clip to constraints
            position = max(self.min_position, min(self.max_position, kelly_final))
            
            return position
            
        except Exception as e:
            logger.debug(f"Kelly calculation error: {e}")
            return self.min_position
    
    def _normalize_positions(self, positions: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize positions to portfolio constraints
        Ensure total doesn't exceed 100% and respects min/max bounds
        """
        try:
            # Apply min/max constraints
            constrained = {}
            for symbol, pos in positions.items():
                constrained[symbol] = max(self.min_position,
                                         min(self.max_position, pos))
            
            # Calculate total
            total = sum(constrained.values())
            
            # Normalize if total > 1.0
            if total > 1.0:
                scale_factor = 0.95 / total  # Leave 5% cash buffer
                constrained = {
                    symbol: pos * scale_factor
                    for symbol, pos in constrained.items()
                }
            
            return constrained
            
        except Exception as e:
            logger.error(f"Position normalization error: {e}")
            return positions
    
    def _uniform_allocation(self, symbols: List[str]) -> Dict[str, float]:
        """Default: uniform allocation"""
        if not symbols:
            return {}
        
        equal_weight = min(self.max_position, 1.0 / len(symbols))
        return {symbol: equal_weight for symbol in symbols}
    
    def get_position_summary(self, positions: Dict[str, float]) -> Dict:
        """Summarize portfolio positions"""
        total_allocated = sum(positions.values())
        cash_buffer = 1.0 - total_allocated
        
        return {
            'total_positions': len(positions),
            'total_allocated': float(total_allocated),
            'cash_buffer': float(cash_buffer),
            'max_position': max(positions.values()) if positions else 0,
            'min_position': min(positions.values()) if positions else 0,
            'kelly_fraction': float(self.kelly_fraction),
            'positions': positions
        }


logger.info("[KELLY OPTIMIZER] Position sizing optimizer loaded")
