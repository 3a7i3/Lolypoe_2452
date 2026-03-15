from .strategy_evolution_engine import StrategyEvolutionEngine

class MetaStrategyAI:
    def __init__(self, strategy_engine: StrategyEvolutionEngine):
        self.strategy_engine = strategy_engine

    def select_best_strategies(self, strategies):
        ranked = sorted(strategies, key=lambda x: x['score'], reverse=True)
        top_strategies = ranked[:10]
        return top_strategies

    def combine_strategies(self, strategies):
        combined = {}
        total_score = sum(s['score'] for s in strategies)
        for s in strategies:
            combined[s['name']] = s['score'] / total_score if total_score else 0
        return combined
