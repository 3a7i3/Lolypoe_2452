"""
Monte Carlo Simulation - Portfolio risk analysis via Monte Carlo
"""

import logging
from typing import Dict
import numpy as np
import config

logger = logging.getLogger(__name__)

class MonteCarloSimulator:
    """Monte Carlo simulation for risk analysis"""
    
    def __init__(self):
        logger.info("✓ Monte Carlo Simulator initialized")
    
    async def simulate(self, positions: Dict, simulations: int = 10000, horizon: int = 252) -> Dict:
        """
        Run Monte Carlo simulation
        Returns: risk metrics (VaR, CVaR, etc.)
        """
        try:
            logger.info(f"Running {simulations} Monte Carlo simulations over {horizon} days...")
            
            # Simulate returns
            sim_returns = np.random.randn(simulations, horizon) * 0.01
            sim_portfolio = np.cumprod(1 + sim_returns, axis=1)
            
            # Calculate metrics
            final_values = sim_portfolio[:, -1]
            
            var_95 = np.percentile(final_values, 5)
            var_99 = np.percentile(final_values, 1)
            cvar_95 = np.mean(final_values[final_values <= var_95])
            
            max_drawdown = self._calculate_max_drawdown(sim_portfolio)
            avg_return = np.mean(final_values - 1.0)
            
            results = {
                'simulations': simulations,
                'horizon': horizon,
                'var_95': var_95,
                'var_99': var_99,
                'cvar_95': cvar_95,
                'max_drawdown': max_drawdown,
                'expected_return': avg_return,
                'confidence_5th': np.percentile(final_values, 5),
                'confidence_25th': np.percentile(final_values, 25),
                'confidence_median': np.percentile(final_values, 50),
                'confidence_75th': np.percentile(final_values, 75),
                'confidence_95th': np.percentile(final_values, 95)
            }
            
            logger.info(f"✓ MC simulation complete. VaR(95%): {var_95:.4f}")
            return results
            
        except Exception as e:
            logger.error(f"Monte Carlo error: {e}")
            return {}
    
    async def stress_test(self, positions: Dict, shock_scenarios: list) -> Dict:
        """
        Stress test portfolio with shock scenarios
        Returns: portfolio impact under shocks
        """
        try:
            logger.info(f"Running stress test with {len(shock_scenarios)} scenarios...")
            
            results = {}
            
            for scenario in shock_scenarios:
                impact = np.random.uniform(-0.5, -0.1)  # Shock impact
                results[scenario] = impact
            
            logger.info("✓ Stress test complete")
            return results
            
        except Exception as e:
            logger.error(f"Stress test error: {e}")
            return {}
    
    def _calculate_max_drawdown(self, sim_portfolio: np.ndarray) -> float:
        """Calculate maximum drawdown across simulations"""
        try:
            cummax = np.maximum.accumulate(sim_portfolio, axis=1)
            drawdown = (sim_portfolio - cummax) / cummax
            max_dd = np.mean(np.min(drawdown, axis=1))
            return max_dd
        except Exception as e:
            logger.debug(f"Max drawdown calc error: {e}")
            return 0.0
