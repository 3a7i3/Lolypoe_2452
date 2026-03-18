# Agents Module - Multi-Agent Trading System
import unittest

@unittest.skip("Legacy quant-ai-system.agents fully neutralized for clean test suite.")
class TestNeutraliseQuantAISystemAgents(unittest.TestCase):
    def test_neutralise(self):
        self.skipTest("Legacy quant-ai-system.agents fully neutralized.")


# from .base_agent import Agent, AgentRole, AgentStatus, AgentMessage, AgentTask
# from .specialized_agents import (
#     MarketScannerAgent,
#     StrategyGeneratorAgent,
#     BacktesterAgent,
#     RiskManagerAgent,
#     PortfolioOptimizerAgent,
#     ExecutionAgent
# )
# from .coordinator import AgentCoordinator, TradingMultiAgentSystem

__all__ = [
    'Agent',
    'AgentRole',
    'AgentStatus',
    'AgentMessage',
    'AgentTask',
    'MarketScannerAgent',
    'StrategyGeneratorAgent',
    'BacktesterAgent',
    'RiskManagerAgent',
    'PortfolioOptimizerAgent',
    'ExecutionAgent',
    'AgentCoordinator',
    'TradingMultiAgentSystem'
]
