"""Kelly Criterion Optimizer"""

import numpy as np
import pandas as pd
from typing import Dict, List
from utils.logger import logger

class KellyOptimizer:
    """
    Kelly Criterion Portfolio Optimization
    ======================================
    f* = (bp - q) / b
    
    Where:
    - f* = Optimal fraction of bankroll to wager
    - b = Odds (profit if win / loss if lose)
    - p = Probability of win
    - q = Probability of loss (1 - p)
    """
    
    def optimize(self, signals: Dict, historical_data: Dict = None) -> Dict:
        """
        Calculate Kelly fraction allocation for each position.
        """
        logger.info("Calculating Kelly criterion allocations...")
        
        allocations = {}
        total_kelly_fraction = 0
        
        for symbol, signal_data in signals.items():
            confidence = signal_data['ensemble']['confidence']
            action = signal_data['ensemble']['action']
            
            if action == 'HOLD' or confidence < 0.5:
                allocations[symbol] = {'kelly_fraction': 0, 'size': 0}
                continue
            
            # Calculate win probability and odds
            win_prob = confidence
            loss_prob = 1 - confidence
            
            # Estimate odds (simplified: assume 2:1 profit/loss ratio)
            odds = 2.0  # b parameter
            
            # Kelly formula
            kelly_fraction = self._calculate_kelly(
                win_prob=win_prob,
                loss_prob=loss_prob,
                odds=odds
            )
            
            # Apply Kelly fraction
            allocations[symbol] = {
                'kelly_fraction': kelly_fraction,
                'size': kelly_fraction,
                'win_probability': win_prob,
                'odds': odds
            }
            
            total_kelly_fraction += kelly_fraction
        
        # Apply Kelly limit (max 25% of capital per position for safety)
        kelly_limit = 0.25
        for symbol in allocations:
            if allocations[symbol]['kelly_fraction'] > kelly_limit:
                allocations[symbol]['kelly_fraction'] = kelly_limit
        
        # Normalize allocations
        total = sum(a['kelly_fraction'] for a in allocations.values())
        if total > 0:
            for symbol in allocations:
                allocations[symbol]['normalized_fraction'] = allocations[symbol]['kelly_fraction'] / total
        
        logger.info(f"✓ Kelly allocation calculated for {len(allocations)} symbols")
        
        return allocations
    
    def _calculate_kelly(self, win_prob: float, loss_prob: float, odds: float) -> float:
        """
        Kelly criterion: f* = (bp - q) / b
        
        Parameters:
        - win_prob: Probability of winning
        - loss_prob: Probability of losing
        - odds: Ratio of profit to loss (bet odds)
        
        Returns:
        - Kelly fraction (0-1)
        """
        # f* = (bp - q) / b
        numerator = (odds * win_prob) - loss_prob
        denominator = odds
        
        kelly_fraction = numerator / denominator if denominator != 0 else 0
        
        # Apply Kelly fraction cap (half Kelly for safety)
        kelly_fraction = max(0, min(kelly_fraction, 1))
        
        # Use half-Kelly for risk management (more conservative)
        kelly_fraction = kelly_fraction * 0.5
        
        return kelly_fraction
    
    def calculate_growth_rate(self, kelly_fraction: float, win_prob: float, 
                            odds: float) -> float:
        """
        Calculate expected logarithmic growth rate.
        
        g = p * log(1 + f*b) + q * log(1 - f*)
        """
        loss_prob = 1 - win_prob
        
        growth = (
            win_prob * np.log(1 + kelly_fraction * odds) +
            loss_prob * np.log(1 - kelly_fraction)
        )
        
        return growth
    
    def simulate_kelly_vs_fixed(self, kelly_fraction: float, initial_capital: float,
                               win_prob: float, odds: float, num_bets: int) -> Dict:
        """
        Simulate Kelly betting vs fixed fraction betting.
        """
        # Kelly betting
        kelly_capital = initial_capital
        kelly_values = [kelly_capital]
        
        # Fixed fraction betting (e.g., 5%)
        fixed_fraction = 0.05
        fixed_capital = initial_capital
        fixed_values = [fixed_capital]
        
        # Simulate
        for i in range(num_bets):
            # Random outcome
            is_win = np.random.rand() < win_prob
            
            # Kelly betting
            kelly_bet = kelly_capital * kelly_fraction
            if is_win:
                kelly_capital += kelly_bet * odds
            else:
                kelly_capital -= kelly_bet
            kelly_values.append(kelly_capital)
            
            # Fixed fraction betting
            fixed_bet = fixed_capital * fixed_fraction
            if is_win:
                fixed_capital += fixed_bet * odds
            else:
                fixed_capital -= fixed_bet
            fixed_values.append(fixed_capital)
        
        return {
            'kelly_final': kelly_values[-1],
            'kelly_values': kelly_values,
            'kelly_max_dd': self._max_drawdown(kelly_values),
            'fixed_final': fixed_values[-1],
            'fixed_values': fixed_values,
            'fixed_max_dd': self._max_drawdown(fixed_values),
            'kelly_vs_fixed_ratio': kelly_values[-1] / fixed_values[-1] if fixed_values[-1] != 0 else 0
        }
    
    def _max_drawdown(self, values: List[float]) -> float:
        """Calculate maximum drawdown."""
        running_max = np.maximum.accumulate(values)
        drawdown = (np.array(values) - running_max) / running_max
        return np.min(drawdown)
    
    def optimize_with_correlation(self, returns_df: pd.DataFrame, expected_returns: np.ndarray) -> Dict:
        """
        Optimize Kelly allocation considering correlation between positions.
        """
        logger.info("Optimizing Kelly allocation with correlation adjustment...")
        
        # Calculate correlation matrix
        correlation = returns_df.corr()
        
        # Calculate position-wise Kelly fractions
        kelly_fractions = {}
        
        for symbol in returns_df.columns:
            returns = returns_df[symbol]
            win_rate = (returns > 0).sum() / len(returns)
            
            # Calculate Sharpe ratio as odds estimate
            sharpe = returns.mean() / returns.std() if returns.std() != 0 else 0
            odds = 1 + sharpe
            
            kelly = self._calculate_kelly(win_rate, 1 - win_rate, odds)
            kelly_fractions[symbol] = kelly
        
        # Adjust for correlation (reduce allocation for highly correlated positions)
        adjusted_fractions = {}
        for symbol in kelly_fractions:
            avg_correlation = correlation[symbol].mean()
            correlation_penalty = 1 - (avg_correlation * 0.5)  # Penalize positive correlation
            adjusted_fractions[symbol] = kelly_fractions[symbol] * correlation_penalty
        
        logger.info(f"✓ Correlation-adjusted Kelly allocations calculated")
        
        return adjusted_fractions
