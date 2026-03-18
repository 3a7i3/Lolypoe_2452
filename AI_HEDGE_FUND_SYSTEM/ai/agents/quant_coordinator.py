from AI_HEDGE_FUND_SYSTEM.ai.agents.data_agent import DataAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.feature_agent import FeatureAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.strategy_agent import StrategyAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.backtest_agent import BacktestAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.risk_agent import RiskAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.portfolio_agent import PortfolioAgent
from AI_HEDGE_FUND_SYSTEM.ai.agents.execution_agent import ExecutionAgent

class QuantCoordinator:
    def __init__(self):
        self.data_agent = DataAgent()
        self.feature_agent = FeatureAgent()
        self.strategy_agent = StrategyAgent()
        self.backtest_agent = BacktestAgent()
        self.risk_agent = RiskAgent()
        self.portfolio_agent = PortfolioAgent()
        self.execution_agent = ExecutionAgent()

    def run_cycle(self):
        data = self.data_agent.fetch_market_data()
        features = self.feature_agent.build_features(data)
        strategies = self.strategy_agent.create_strategies()
        results = self.backtest_agent.evaluate(strategies, features)
        safe_strategies = self.risk_agent.filter(results)
        allocations = self.portfolio_agent.allocate(safe_strategies)
        self.execution_agent.execute(allocations)
        return allocations
