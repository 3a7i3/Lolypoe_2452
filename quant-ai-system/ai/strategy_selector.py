"""
Strategy Selector
Finds and selects the best strategies
"""

from typing import Dict, List, Any
from ai.strategy_generator import generate_population
from ai.strategy_evaluator import evaluate_population


class StrategySelector:
    """Selects best strategies from generated population"""
    
    def __init__(self, population_size: int = 50, top_k: int = 5):
        self.population_size = population_size
        self.top_k = top_k
        self.history = []
    
    def find_best_strategy(self, market_data: Dict[str, Any], 
                          iterations: int = None) -> Dict[str, Any]:
        """Find the single best strategy"""
        iterations = iterations or self.population_size
        
        best_strategies = self.find_best_strategies(market_data, iterations, k=1)
        
        if best_strategies:
            return best_strategies[0]
        
        return None
    
    def find_best_strategies(self, market_data: Dict[str, Any], 
                             iterations: int = None, k: int = None) -> List[Dict[str, Any]]:
        """Find top K best strategies"""
        
        iterations = iterations or self.population_size
        k = k or self.top_k
        
        # Generate population
        strategies = generate_population(iterations)
        
        # Evaluate all strategies
        results = evaluate_population(strategies, market_data)
        
        # Store history
        self.history.append({
            'timestamp': None,
            'best_score': results[0]['score'] if results else 0,
            'population_size': iterations,
            'evaluation_count': len(results)
        })
        
        # Return top K
        return results[:k]
    
    def evolve_strategies(self, market_data: Dict[str, Any], 
                         generations: int = 10, population_size: int = 50) -> List[Dict[str, Any]]:
        """Evolve strategies using genetic algorithm"""
        
        best_strategies = []
        
        for gen in range(generations):
            # Generate and evaluate population
            strategies = generate_population(population_size)
            results = evaluate_population(strategies, market_data)
            
            # Select top performers
            top_performers = results[:population_size // 2]
            best_strategies = results[:self.top_k]
            
            print(f"Generation {gen + 1}: Best score = {results[0]['score']:.2f}")
        
        return best_strategies


# Convenience functions
_selector = StrategySelector()


def find_best_strategy(market_data: Dict[str, Any], iterations: int = 50) -> Dict[str, Any]:
    """Find the single best strategy"""
    return _selector.find_best_strategy(market_data, iterations)


def find_best_strategies(market_data: Dict[str, Any], 
                        iterations: int = 50, k: int = 5) -> List[Dict[str, Any]]:
    """Find top K best strategies"""
    return _selector.find_best_strategies(market_data, iterations, k)


def evolve_strategies(market_data: Dict[str, Any], 
                     generations: int = 10, population_size: int = 50) -> List[Dict[str, Any]]:
    """Evolve strategies using genetic algorithm"""
    return _selector.evolve_strategies(market_data, generations, population_size)
