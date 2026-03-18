import pandas as pd
from strategy_factory.generator import StrategyGenerator
from strategy_factory.backtester import Backtester
from strategy_factory.fitness import FitnessEvaluator
from strategy_factory.evolution import EvolutionEngine

def test_full_cycle():
    # Génère des stratégies
    generator = StrategyGenerator()
    strategies = generator.generate(10)
    # DataFrame factice
    df = pd.DataFrame({
        "momentum": [0.2, 0.3, 0.5, 0.7, 0.9, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7],
        "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]
    })
    backtester = Backtester()
    fitness = FitnessEvaluator()
    evolution = EvolutionEngine()
    # Backtest et fitness
    scores = []
    for strat in strategies:
        pnl = backtester.evaluate(strat, df)
        scores.append(pnl)
    # Évolution
    new_strategies = evolution.evolve(strategies, scores)
    assert len(new_strategies) > 0
    print("Cycle complet OK. Nouvelles stratégies:", len(new_strategies))

if __name__ == "__main__":
    test_full_cycle()
