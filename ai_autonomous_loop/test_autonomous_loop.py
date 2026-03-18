# Correction import dynamique pour exécution directe
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_autonomous_loop.autonomous_research_loop import AutonomousResearchLoop
from ai_autonomous_loop.strategy_memory import StrategyMemory
from ai_autonomous_loop.performance_feedback import PerformanceFeedback
from ai_autonomous_loop.research_scheduler import ResearchScheduler
from ai_autonomous_loop.auto_optimizer import HyperparameterOptimizer, AIModelTrainer, ReinforcementLearningEngine

# Placeholders pour les modules du pipeline
class DummyResearchAgent:
    def generate_hypotheses(self):
        return ["momentum_breakout", "mean_reversion"]

class DummyStrategyFarm:
    def generate(self, hypotheses):
        return [{"id": h, "params": {}} for h in hypotheses]

class DummyBacktestEngine:
    def run(self, strategies):
        return [{"id": s["id"], "sharpe": 1.2, "return": 0.15} for s in strategies]

class DummyBotDoctor:
    def validate(self, results):
        return [r for r in results if r["sharpe"] > 1]

class DummyPortfolioEngine:
    def update(self, approved):
        print(f"Portfolio updated with: {approved}")

# Instanciation des modules
research_agent = DummyResearchAgent()
strategy_farm = DummyStrategyFarm()
backtest_engine = DummyBacktestEngine()
bot_doctor = DummyBotDoctor()
portfolio_engine = DummyPortfolioEngine()

loop = AutonomousResearchLoop(research_agent, strategy_farm, backtest_engine, bot_doctor, portfolio_engine)

# Test du cycle autonome avec feedback et action automatique
result = loop.run_cycle()
approved = result["approved"]
feedback = result["feedback"]
action = result["action"]
print("Approved strategies:", approved)
print("Feedback report:", feedback)
print("Action taken:", action)

# Test de la mémoire
memory = StrategyMemory()
for r in approved:
    memory.store(r["id"], r)
print("Best strategies:", memory.get_best())

# Test du feedback
feedback = PerformanceFeedback()
insights = feedback.analyze(approved)
print("Performance feedback:", insights)

# Test de l'auto-optimizer
optimizer = HyperparameterOptimizer(strategy_farm)
optimized = optimizer.optimize(["momentum_breakout"])
print("Optimized hypotheses:", optimized)

# Test du model trainer
model_storage = {}
trainer = AIModelTrainer(model_storage)
model_id = trainer.train([1,2,3,4], model_type="mlp")
print("Trained model id:", model_id)

# Test du RL engine
env = {}  # Placeholder
rl_engine = ReinforcementLearningEngine(env)
rl_result = rl_engine.run("momentum_breakout")
print("RL result:", rl_result)
