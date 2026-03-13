"""Walk-Forward Backtesting Engine"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from utils.logger import logger

class WalkForwardTester:
    """
    Walk-Forward Backtesting
    ========================
    - In-sample optimization period
    - Out-of-sample testing period
    - Parameter stability analysis
    - Out-of-sample performance
    - Transaction costs
    """
    
    def run(self, strategies: List[str], data: Dict, 
            optimization_period: int = 252, test_period: int = 63) -> Dict:
        """
        Execute walk-forward test.
        
        Parameters:
        - strategies: List of strategy names to test
        - data: Market data for all symbols
        - optimization_period: Days for in-sample optimization
        - test_period: Days for out-of-sample testing
        """
        logger.info("Running walk-forward backtest...")
        
        results = {
            'strategies': {},
            'summary': {}
        }
        
        for strategy in strategies:
            logger.info(f"  Testing strategy: {strategy}")
            
            # For first symbol (can be extended to all)
            first_symbol = list(data.keys())[0]
            symbol_data = data[first_symbol]
            
            if isinstance(symbol_data, dict):
                # Convert dict to DataFrame if needed
                symbol_data = pd.DataFrame([symbol_data])
            
            # Run walk-forward test
            wf_results = self._walk_forward_test(
                strategy=strategy,
                data=symbol_data,
                opt_period=optimization_period,
                test_period=test_period
            )
            
            results['strategies'][strategy] = wf_results
        
        # Aggregate results
        results['summary'] = self._aggregate_results(results['strategies'])
        
        logger.info("✓ Walk-forward backtest complete")
        return results
    
    def _walk_forward_test(self, strategy: str, data: pd.DataFrame,
                          opt_period: int, test_period: int) -> Dict:
        """
        Single strategy walk-forward test.
        """
        if len(data) < (opt_period + test_period):
            logger.warning(f"Insufficient data for {strategy}: need {opt_period + test_period}, have {len(data)}")
            return {'error': 'Insufficient data'}
        
        in_sample_pnl = []
        out_sample_pnl = []
        parameter_sets = []
        
        # Walk forward through data
        for i in range(opt_period, len(data) - test_period, test_period):
            # In-sample: optimize parameters
            in_sample = data.iloc[i-opt_period:i]
            best_params = self._optimize_parameters(strategy, in_sample)
            parameter_sets.append(best_params)
            
            # Get in-sample performance
            in_pnl = self._backtest_with_params(strategy, in_sample, best_params)
            in_sample_pnl.append(in_pnl)
            
            # Out-of-sample: test with optimized parameters
            out_sample = data.iloc[i:i+test_period]
            out_pnl = self._backtest_with_params(strategy, out_sample, best_params)
            out_sample_pnl.append(out_pnl)
        
        # Calculate degradation
        is_return = np.mean(in_sample_pnl) if in_sample_pnl else 0
        oos_return = np.mean(out_sample_pnl) if out_sample_pnl else 0
        degradation = (is_return - oos_return) / abs(is_return) if is_return != 0 else 0
        
        return {
            'in_sample_return': is_return,
            'out_of_sample_return': oos_return,
            'degradation': degradation,
            'in_sample_pnl': in_sample_pnl,
            'out_sample_pnl': out_sample_pnl,
            'parameter_sets': parameter_sets,
            'parameter_stability': self._calculate_stability(parameter_sets),
        }
    
    def _optimize_parameters(self, strategy: str, data: pd.DataFrame) -> Dict:
        """Optimize parameters for given strategy on in-sample data."""
        # Simplified optimization - extend with actual optimization logic
        
        if strategy == 'trend_following':
            return {
                'sma_short': 20,
                'sma_long': 50,
                'rsi_threshold': 70
            }
        elif strategy == 'mean_reversion':
            return {
                'rsi_overbought': 70,
                'rsi_oversold': 30,
                'bb_period': 20
            }
        elif strategy == 'breakout':
            return {
                'lookback_period': 20,
                'volume_multiplier': 1.5
            }
        
        return {}
    
    def _backtest_with_params(self, strategy: str, data: pd.DataFrame, 
                             params: Dict) -> float:
        """Backtest strategy with given parameters."""
        # Simplified backtest return
        if len(data) < 2:
            return 0
        
        # Return simple price change percentage
        return (data.iloc[-1:].values[0][0] - data.iloc[0:1].values[0][0]) / data.iloc[0:1].values[0][0]
    
    def _calculate_stability(self, parameter_sets: List[Dict]) -> float:
        """Calculate parameter stability across walk-forward periods."""
        if not parameter_sets or len(parameter_sets) < 2:
            return 1.0
        
        # Measure coefficient of variation in parameters
        stability_scores = []
        
        for param_name in parameter_sets[0].keys():
            values = [p.get(param_name, 0) for p in parameter_sets]
            if np.mean(values) != 0:
                cv = np.std(values) / abs(np.mean(values))
                stability_scores.append(1 / (1 + cv))  # Convert to 0-1 scale
        
        return np.mean(stability_scores) if stability_scores else 0.5
    
    def _aggregate_results(self, strategy_results: Dict) -> Dict:
        """Aggregate results across all strategies."""
        summary = {
            'best_strategy': None,
            'best_oos_return': -np.inf,
            'avg_degradation': 0,
            'strategy_ranking': []
        }
        
        degradations = []
        rankings = []
        
        for strategy, results in strategy_results.items():
            if 'error' in results:
                continue
            
            oos_return = results.get('out_of_sample_return', 0)
            degradation = results.get('degradation', 0)
            
            degradations.append(degradation)
            rankings.append({
                'strategy': strategy,
                'oos_return': oos_return,
                'degradation': degradation,
                'stability': results.get('parameter_stability', 0)
            })
            
            if oos_return > summary['best_oos_return']:
                summary['best_oos_return'] = oos_return
                summary['best_strategy'] = strategy
        
        summary['avg_degradation'] = np.mean(degradations) if degradations else 0
        summary['strategy_ranking'] = sorted(rankings, key=lambda x: x['oos_return'], reverse=True)
        
        return summary
