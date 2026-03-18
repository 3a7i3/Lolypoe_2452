
from .generator import StrategyGenerator
from .backtester import StrategyBacktester
from .scorer import StrategyScorer
from .selector import StrategySelector
# --- Ajout IA ---
from strategy_ai.dataset_builder import DatasetBuilder
from strategy_ai.model import StrategyAIModel
from strategy_ai.signal_generator import AISignalGenerator

class StrategyFarm:
    def __init__(self, use_ai_signal=True):
        self.generator = StrategyGenerator()
        self.backtester = StrategyBacktester()
        self.scorer = StrategyScorer()
        self.selector = StrategySelector()
        self.use_ai_signal = use_ai_signal
        if use_ai_signal:
            self.dataset_builder = DatasetBuilder()
            self.ai_model = StrategyAIModel()
            self.ai_signal_engine = None

    def run(self, df, n_strategies=100, top=10):
        strategies = self.generator.generate(n_strategies)
        scores = []
        for strat in strategies:
            trades = self.backtester.test(strat, df)
            score = self.scorer.score(trades)
            scores.append(score)
        # --- Ajout IA ---
        if self.use_ai_signal:
            dataset = self.dataset_builder.build(df)
            self.ai_model.train(dataset)
            if self.ai_signal_engine is None:
                self.ai_signal_engine = AISignalGenerator(self.ai_model)
            ai_signal = self.ai_signal_engine.generate(df)
            # Ajoute le signal IA comme stratégie spéciale
            ai_strat = {"type": "AI", "desc": "AI Signal", "logic": "AI", "position_size": 0.2}
            ai_score = 0.5 if ai_signal == "HOLD" else (1.0 if ai_signal == "BUY" else -1.0)
            strategies.append(ai_strat)
            scores.append(ai_score)
        best = self.selector.select(strategies, scores, top=top)
        return best
