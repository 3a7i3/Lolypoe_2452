"""
Optimizer
Portfolio optimization and strategy parameter tuning
"""

from typing import Dict, List, Any, Callable
from dataclasses import dataclass
import numpy as np


@dataclass
class OptimizationResult:
    """Result of optimization run"""
    best_params: Dict[str, float]
    best_score: float
    iterations: int
    improvement: float  # vs initial


class GeneticAlgorithmOptimizer:
    """Genetic algorithm optimizer for strategy parameters"""
    
    def __init__(self, population_size: int = 50, generations: int = 20,
                 mutation_rate: float = 0.1, crossover_rate: float = 0.9):
        """
        Initialize GA optimizer
        Args:
            population_size: Population size
            generations: Number of generations
            mutation_rate: Mutation probability
            crossover_rate: Crossover probability
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        self.history = []
    
    def optimize_parameters(self, objective_func: Callable, param_ranges: Dict[str, tuple],
                          maximize: bool = True) -> OptimizationResult:
        """
        Optimize parameters using genetic algorithm
        Args:
            objective_func: Function to maximize/minimize
            param_ranges: Dict of param -> (min, max)
            maximize: Whether to maximize (True) or minimize (False)
        Returns:
            OptimizationResult
        """
        # Initialize population
        population = self._initialize_population(param_ranges)
        
        best_fitness = None
        best_solution = None
        
        for gen in range(self.generations):
            # Evaluate population
            fitness_scores = [
                objective_func(self._dict_from_array(params, param_ranges))
                for params in population
            ]
            
            # Track best
            if maximize:
                best_idx = np.argmax(fitness_scores)
            else:
                best_idx = np.argmin(fitness_scores)
            
            current_best = fitness_scores[best_idx]
            
            if best_fitness is None or (maximize and current_best > best_fitness) or \
               (not maximize and current_best < best_fitness):
                best_fitness = current_best
                best_solution = population[best_idx].copy()
            
            # Selection (tournament)
            selected = self._tournament_selection(population, fitness_scores, 
                                                 self.population_size // 2, maximize)
            
            # Crossover and mutation
            new_population = selected.copy()
            while len(new_population) < self.population_size:
                parent1 = selected[np.random.randint(len(selected))]
                parent2 = selected[np.random.randint(len(selected))]
                
                if np.random.rand() < self.crossover_rate:
                    offspring = self._crossover(parent1, parent2)
                else:
                    offspring = parent1.copy()
                
                if np.random.rand() < self.mutation_rate:
                    offspring = self._mutate(offspring, param_ranges)
                
                new_population.append(offspring)
            
            population = new_population[:self.population_size]
            
            self.history.append({
                'generation': gen,
                'best_fitness': current_best,
                'avg_fitness': np.mean(fitness_scores)
            })
        
        result = OptimizationResult(
            best_params=self._dict_from_array(best_solution, param_ranges),
            best_score=best_fitness,
            iterations=self.generations,
            improvement=best_fitness
        )
        
        return result
    
    def _initialize_population(self, param_ranges: Dict[str, tuple]) -> List[np.ndarray]:
        """Initialize random population"""
        population = []
        for _ in range(self.population_size):
            individual = np.array([
                np.random.uniform(min_val, max_val)
                for _, (min_val, max_val) in param_ranges.items()
            ])
            population.append(individual)
        return population
    
    def _tournament_selection(self, population: List[np.ndarray],
                             fitness_scores: List[float], num_select: int,
                             maximize: bool = True) -> List[np.ndarray]:
        """Tournament selection"""
        selected = []
        for _ in range(num_select):
            # Random tournament of 3
            indices = np.random.choice(len(population), 3, replace=False)
            tournament_fitness = [fitness_scores[i] for i in indices]
            
            if maximize:
                winner_idx = indices[np.argmax(tournament_fitness)]
            else:
                winner_idx = indices[np.argmin(tournament_fitness)]
            
            selected.append(population[winner_idx].copy())
        
        return selected
    
    def _crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> np.ndarray:
        """Single-point crossover"""
        crossover_point = np.random.randint(1, len(parent1))
        offspring = np.concatenate([
            parent1[:crossover_point],
            parent2[crossover_point:]
        ])
        return offspring
    
    def _mutate(self, individual: np.ndarray, param_ranges: Dict[str, tuple]) -> np.ndarray:
        """Gaussian mutation"""
        mutated = individual.copy()
        for i, (param, (min_val, max_val)) in enumerate(param_ranges.items()):
            # Gaussian mutation
            mutation = np.random.normal(0, (max_val - min_val) * 0.1)
            mutated[i] += mutation
            # Clip to bounds
            mutated[i] = np.clip(mutated[i], min_val, max_val)
        return mutated
    
    def _dict_from_array(self, array: np.ndarray, param_ranges: Dict[str, tuple]) -> Dict[str, float]:
        """Convert array to parameter dictionary"""
        params = {}
        for i, param_name in enumerate(param_ranges.keys()):
            params[param_name] = float(array[i])
        return params


class PortfolioOptimizer:
    """Portfolio optimization using mean-variance"""
    
    def __init__(self):
        self.history = []
    
    def optimize_weights(self, returns: np.ndarray, target_return: float = None,
                        target_volatility: float = None) -> np.ndarray:
        """
        Optimize portfolio weights
        Args:
            returns: Historical returns (n_assets x n_periods)
            target_return: Target portfolio return (optional)
            target_volatility: Target portfolio volatility (optional)
        Returns:
            Optimized weights (sum = 1)
        """
        n_assets = returns.shape[0]
        
        # Calculate covariance matrix
        cov_matrix = np.cov(returns)
        mean_returns = np.mean(returns, axis=1)
        
        # Simple approach: inverse volatility weighting
        volatilities = np.std(returns, axis=1)
        inv_vol = 1 / (volatilities + 1e-6)
        weights = inv_vol / np.sum(inv_vol)
        
        return weights
    
    def calculate_efficient_frontier(self, returns: np.ndarray,
                                    num_portfolios: int = 100) -> List[Dict[str, float]]:
        """Calculate efficient frontier"""
        frontier = []
        
        for i in range(num_portfolios):
            weights = np.random.dirichlet(np.ones(returns.shape[0]))
            
            portfolio_return = np.mean(np.dot(weights, returns))
            portfolio_vol = np.std(np.dot(weights, returns))
            
            frontier.append({
                'return': portfolio_return,
                'volatility': portfolio_vol,
                'weights': weights
            })
        
        return frontier


# Convenience functions
_ga_optimizer = None
_portfolio_optimizer = None


def initialize_ga_optimizer(population_size: int = 50,
                            generations: int = 20) -> GeneticAlgorithmOptimizer:
    """Initialize GA optimizer"""
    global _ga_optimizer
    _ga_optimizer = GeneticAlgorithmOptimizer(
        population_size=population_size,
        generations=generations
    )
    return _ga_optimizer


def get_ga_optimizer() -> GeneticAlgorithmOptimizer:
    """Get GA optimizer"""
    global _ga_optimizer
    if _ga_optimizer is None:
        _ga_optimizer = GeneticAlgorithmOptimizer()
    return _ga_optimizer


def initialize_portfolio_optimizer() -> PortfolioOptimizer:
    """Initialize portfolio optimizer"""
    global _portfolio_optimizer
    _portfolio_optimizer = PortfolioOptimizer()
    return _portfolio_optimizer


def get_portfolio_optimizer() -> PortfolioOptimizer:
    """Get portfolio optimizer"""
    global _portfolio_optimizer
    if _portfolio_optimizer is None:
        _portfolio_optimizer = PortfolioOptimizer()
    return _portfolio_optimizer
