
from AI_HEDGE_FUND_SYSTEM.ai.agents.data_agent import DataAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.feature_agent import FeatureAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.strategy_agent import StrategyAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.backtest_agent import BacktestAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.risk_agent import RiskAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.portfolio_agent import PortfolioAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.execution_agent import ExecutionAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.ai_brain import AIBrain
from AI_HEDGE_FUND_SYSTEM.ai.agents.genetic_evolution import GeneticEvolution
from AI_HEDGE_FUND_SYSTEM.ai.agents.social_agent import SocialAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.monitoring_agent import MonitoringAgent
from AI_HEDGE_FUND_SYSTEM.ai.simulation_matrix.simulation_matrix import SimulationMatrix





class AgentCoordinator:
    def __init__(self):
        self.data_agent = DataAgent()
        self.feature_agent = FeatureAgent()
        self.strategy_agent = StrategyAgent()
        self.backtest_agent = BacktestAgent()
        self.risk_agent = RiskAgent()
        self.portfolio_agent = PortfolioAgent()
        self.execution_agent = ExecutionAgent()
        self.ai_brain = AIBrain()
        self.genetic_evolution = GeneticEvolution()
        self.social_agent = SocialAgent()
        self.monitoring_agent = MonitoringAgent()
        self.simulation_matrix = SimulationMatrix()

    def run_cycle(self):
        data = self.data_agent.fetch_market_data()
        features = self.feature_agent.build_features(data)
        social_signals = self.social_agent.scan()
        strategies = self.strategy_agent.create_strategies()
        improved_strategies = self.ai_brain.learn(strategies, features)
        evolved_strategies = self.genetic_evolution.evolve(improved_strategies)
        results = self.backtest_agent.evaluate(evolved_strategies, features)
        safe_strategies = self.risk_agent.filter(results)
        simulated_strategies = self.simulation_matrix.run_cycle(safe_strategies)
        allocations = self.portfolio_agent.allocate(simulated_strategies)
        self.execution_agent.execute(allocations)
        self.monitoring_agent.track(allocations)
        return allocations
