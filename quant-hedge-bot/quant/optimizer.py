"""
Optimizer - Optimisation des parametres de strategie
"""

from quant.backtester import Backtester
from utils.logger import logger

class Optimizer:
    """Optimise les parametres de strategie via grid search."""
    
    def __init__(self, data, strategy_func):
        self.data = data
        self.strategy_func = strategy_func
        self.results = []
    
    def optimize(self, param_grid):
        """Lance l'optimisation."""
        logger.info(f"Debut optimisation avec {len(param_grid)} combinaisons...")
        
        for i, params in enumerate(param_grid):
            if (i + 1) % 10 == 0:
                logger.info(f"Progres: {i+1}/{len(param_grid)}")
            
            # Backtester avec ces params
            backtester = Backtester()
            results = backtester.run_backtest(self.data, self.strategy_func)
            
            results['params'] = params
            self.results.append(results)
        
        logger.info("Optimisation terminee")
        return self.get_best_parameters()
    
    def get_best_parameters(self):
        """Retourne les meilleurs parametres."""
        if not self.results:
            return None
        
        # Sort par ROI
        sorted_results = sorted(self.results, key=lambda x: x['total_return_percent'], reverse=True)
        
        best = sorted_results[0]
        top_5 = sorted_results[:5]
        
        return {
            'best_params': best['params'],
            'best_roi': best['total_return_percent'],
            'top_5': [{'params': r['params'], 'roi': r['total_return_percent']} for r in top_5]
        }
