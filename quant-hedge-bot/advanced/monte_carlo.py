"""Monte Carlo Simulation Engine"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List
from utils.logger import logger

class MonteCarloSimulator:
    """
    Monte Carlo Simulation for Portfolio Analysis
    ==============================================
    - Expected return distributions
    - Value at Risk (VaR)
    - Conditional Value at Risk (CVaR)
    - Drawdown analysis
    - Confidence intervals
    """
    
    def __init__(self):
        self.num_simulations = 10000
        self.confidence_level = 0.95
    
    def simulate(self, returns: np.ndarray, num_simulations: int = 10000, 
                days: int = 252, drift: float = 0.0) -> Dict:
        """
        Run Monte Carlo simulation of portfolio performance.
        
        Parameters:
        - returns: Historical returns array
        - num_simulations: Number of simulation paths
        - days: Number of days to forecast
        - drift: Expected drift (mean return)
        
        Returns:
        - Dictionary with simulation results
        """
        logger.info(f"Running {num_simulations} Monte Carlo simulations for {days} days...")
        
        # Calculate statistics
        daily_return = np.mean(returns)
        daily_volatility = np.std(returns)
        
        if drift == 0.0:
            drift = daily_return
        
        # Initialize simulation array
        price_paths = np.zeros((num_simulations, days + 1))
        price_paths[:, 0] = 100  # Start at 100
        
        # Run simulations
        for t in range(1, days + 1):
            random_returns = np.random.normal(
                loc=drift,
                scale=daily_volatility,
                size=num_simulations
            )
            price_paths[:, t] = price_paths[:, t-1] * (1 + random_returns)
        
        # Calculate metrics
        final_prices = price_paths[:, -1]
        total_returns = (final_prices - 100) / 100
        
        # Value at Risk
        var_95 = np.percentile(total_returns, 5)
        var_99 = np.percentile(total_returns, 1)
        
        # Conditional Value at Risk (Expected Shortfall)
        cvar_95 = total_returns[total_returns <= var_95].mean()
        cvar_99 = total_returns[total_returns <= var_99].mean()
        
        # Confidence intervals
        ci_5 = np.percentile(final_prices, 5)
        ci_25 = np.percentile(final_prices, 25)
        ci_50 = np.percentile(final_prices, 50)
        ci_75 = np.percentile(final_prices, 75)
        ci_95 = np.percentile(final_prices, 95)
        
        # Maximum drawdown analysis
        max_drawdowns = np.zeros(num_simulations)
        for i in range(num_simulations):
            running_max = np.maximum.accumulate(price_paths[i, :])
            drawdown = (price_paths[i, :] - running_max) / running_max
            max_drawdowns[i] = np.min(drawdown)
        
        avg_max_dd = np.mean(max_drawdowns)
        worst_dd = np.min(max_drawdowns)
        
        results = {
            'num_simulations': num_simulations,
            'forecast_days': days,
            'price_paths': price_paths,
            'final_prices': final_prices,
            'total_returns': total_returns,
            
            # Return statistics
            'expected_return': np.mean(total_returns),
            'return_std': np.std(total_returns),
            'return_median': np.median(total_returns),
            'return_min': np.min(total_returns),
            'return_max': np.max(total_returns),
            
            # Risk metrics
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            
            # Confidence intervals
            'confidence_interval_5': ci_5,
            'confidence_interval_25': ci_25,
            'confidence_interval_50': ci_50,
            'confidence_interval_75': ci_75,
            'confidence_interval_95': ci_95,
            
            # Drawdown analysis
            'avg_max_drawdown': avg_max_dd,
            'worst_drawdown': worst_dd,
            'max_drawdowns': max_drawdowns,
            
            # Win rate
            'win_rate': (total_returns > 0).sum() / num_simulations,
        }
        
        logger.info(f"✓ Simulations complete")
        logger.info(f"  Expected Return: {results['expected_return']:.2%}")
        logger.info(f"  VaR (95%): {results['var_95']:.2%}")
        logger.info(f"  CVaR (95%): {results['cvar_95']:.2%}")
        logger.info(f"  Win Rate: {results['win_rate']:.1%}")
        
        return results
    
    def stress_test(self, returns: np.ndarray, shock_magnitude: float = 0.2) -> Dict:
        """
        Stress test portfolio with market shock.
        """
        logger.info(f"Running stress test with {shock_magnitude:.1%} shock...")
        
        shocked_returns = returns * (1 - shock_magnitude)
        
        results = self.simulate(shocked_returns, num_simulations=5000, days=30)
        
        logger.info(f"✓ Stress test complete")
        logger.info(f"  Shocked Expected Return: {results['expected_return']:.2%}")
        logger.info(f"  Worst Case Drawdown: {results['worst_drawdown']:.2%}")
        
        return results
    
    def scenario_analysis(self, returns: np.ndarray) -> Dict:
        """
        Multiple scenario analysis:
        - Base case
        - Bull market
        - Bear market
        - Crash scenario
        """
        logger.info("Running scenario analysis...")
        
        scenarios = {
            'base_case': self.simulate(returns, days=252),
            'bull_market': self.simulate(returns * 1.5, days=252),
            'bear_market': self.simulate(returns * 0.5, days=252),
            'crash': self.simulate(returns * -1, num_simulations=5000, days=30),
        }
        
        logger.info("✓ Scenario analysis complete")
        
        return scenarios
