"""
Multi-Agent Coordinator
Manages inter-agent communication and orchestration
"""

from typing import Dict, List, Any, Optional
from agents.base_agent import Agent, AgentMessage
from datetime import datetime
import logging
import asyncio
from collections import defaultdict


class AgentCoordinator:
    """Central coordinator for multi-agent system"""
    
    def __init__(self):
        """Initialize coordinator"""
        self.agents: Dict[str, Agent] = {}
        self.message_broker: Dict[str, List[AgentMessage]] = defaultdict(list)
        self.execution_history = []
        self.logger = logging.getLogger("AgentCoordinator")
        
        self.logger.info("🎛️  AgentCoordinator initialized")
    
    def register_agent(self, agent: Agent):
        """Register an agent with the coordinator"""
        self.agents[agent.agent_id] = agent
        self.logger.info(f"✅ Agent registered: {agent.name} (ID: {agent.agent_id})")
    
    def register_agents(self, agents: List[Agent]):
        """Register multiple agents"""
        for agent in agents:
            self.register_agent(agent)
        self.logger.info(f"✅ Registered {len(agents)} agents")
    
    async def route_messages(self):
        """Route messages between agents"""
        for agent in self.agents.values():
            # Get all outgoing messages
            while agent.outbox:
                message = agent.outbox.pop(0)
                
                # Store in broker
                self.message_broker[message.receiver_id].append(message)
                self.logger.debug(f"📨 Message routed: {message.sender_id} → {message.receiver_id}")
        
        # Deliver messages to agents
        for agent_id, messages in self.message_broker.items():
            if agent_id in self.agents:
                for message in messages:
                    self.agents[agent_id].receive_message(message)
        
        # Clear broker
        self.message_broker.clear()
    
    async def execute_agents(self, data: Dict[str, Any], 
                            agent_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute agents in parallel
        Args:
            data: Input data for agents
            agent_ids: Specific agents to execute (None = all)
        Returns:
            Execution results
        """
        agents_to_run = []
        
        if agent_ids:
            agents_to_run = [self.agents[aid] for aid in agent_ids if aid in self.agents]
        else:
            agents_to_run = list(self.agents.values())
        
        self.logger.info(f"🚀 Executing {len(agents_to_run)} agents in parallel...")
        
        # Run agents concurrently
        tasks = [agent.run(data) for agent in agents_to_run]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Route any messages between agents
        await self.route_messages()
        
        return {
            'agents_executed': len(agents_to_run),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def execute_sequential(self, agent_ids: List[str], 
                                data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute agents sequentially (with message passing)
        Args:
            agent_ids: Agents to execute in order
            data: Initial input data
        Returns:
            Results from each agent
        """
        results = []
        current_data = data.copy()
        
        self.logger.info(f"🔄 Executing {len(agent_ids)} agents sequentially...")
        
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                self.logger.warning(f"⚠️ Agent {agent_id} not found")
                continue
            
            agent = self.agents[agent_id]
            
            # Execute agent
            result = await agent.run(current_data)
            results.append(result)
            
            # Route messages
            await self.route_messages()
            
            # Use result as input for next agent
            current_data.update(result)
        
        return results
    
    def get_agent_status(self, agent_id: str = None) -> Dict[str, Any]:
        """Get status of agent(s)"""
        if agent_id:
            if agent_id not in self.agents:
                return {'error': f'Agent {agent_id} not found'}
            return self.agents[agent_id].get_status()
        
        # All agents
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self.agents.items()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'agents_count': len(self.agents),
            'agents': self.get_agent_status(),
            'message_queue_size': sum(len(msgs) for msgs in self.message_broker.values()),
            'executions': len(self.execution_history),
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_all_messages(self):
        """Clear all pending messages"""
        for agent in self.agents.values():
            agent.clear_inbox()
            agent.outbox.clear()
        self.message_broker.clear()
        self.logger.info("✅ All messages cleared")


# Specialized Coordinator for Trading
class TradingMultiAgentSystem:
    """Complete multi-agent trading system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize multi-agent trading system
        Args:
            config: System configuration
        """
        self.config = config or {}
        self.coordinator = AgentCoordinator()
        self.logger = logging.getLogger("TradingMultiAgentSystem")
        
        self.logger.info("🤖 Multi-Agent Trading System V7 initialized")
    
    def setup_agents(self, num_scanner_agents: int = 1,
                    num_strategy_agents: int = 3,
                    num_backtest_agents: int = 5,
                    num_risk_agents: int = 2):
        """
        Setup diverse agent pool
        Args:
            num_scanner_agents: Number of market scanner agents
            num_strategy_agents: Number of strategy generator agents
            num_backtest_agents: Number of backtester agents
            num_risk_agents: Number of risk manager agents
        """
        from agents.specialized_agents import (
            MarketScannerAgent,
            StrategyGeneratorAgent,
            BacktesterAgent,
            RiskManagerAgent,
            PortfolioOptimizerAgent,
            ExecutionAgent
        )
        
        agents = []
        
        # Create scanner agents
        for i in range(num_scanner_agents):
            agents.append(MarketScannerAgent(f"scanner_{i}"))
        
        # Create strategy agents
        for i in range(num_strategy_agents):
            agents.append(StrategyGeneratorAgent(f"strategy_{i}"))
        
        # Create backtest agents
        for i in range(num_backtest_agents):
            agents.append(BacktesterAgent(f"backtest_{i}"))
        
        # Create risk agents
        for i in range(num_risk_agents):
            agents.append(RiskManagerAgent(f"risk_{i}"))
        
        # Create optimizer and execution agents
        agents.append(PortfolioOptimizerAgent("portfolio_optimizer_1"))
        agents.append(ExecutionAgent("execution_1"))
        
        self.coordinator.register_agents(agents)
        
        total_agents = sum([num_scanner_agents, num_strategy_agents, 
                           num_backtest_agents, num_risk_agents, 2])
        
        self.logger.info(f"✅ Setup {total_agents} agents")
    
    async def run_trading_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute complete trading cycle
        Args:
            market_data: Market data input
        Returns:
            Trading cycle results
        """
        self.logger.info("\n" + "="*70)
        self.logger.info("🔄 TRADING CYCLE START")
        self.logger.info("="*70)
        
        # Pipeline:
        # 1. Market Scanners identify opportunities
        # 2. Strategy Generators create strategies
        # 3. Backtester Agents evaluate strategies
        # 4. Risk Managers approve strategies
        # 5. Portfolio Optimizer sizes positions
        # 6. Execution Agent executes trades
        
        cycle_data = {
            'market_data': market_data,
            'population_size': 50,
            'portfolio_value': 100000,
            'max_drawdown': 0.25,
            'max_positions': 20
        }
        
        # Sequential execution with message passing
        agent_pipeline = [
            'scanner_0',
            'strategy_0',
            'backtest_0',
            'risk_0',
            'portfolio_optimizer_1',
            'execution_1'
        ]
        
        results = await self.coordinator.execute_sequential(agent_pipeline, cycle_data)
        
        self.logger.info("\n" + "="*70)
        self.logger.info("✅ TRADING CYCLE COMPLETE")
        self.logger.info("="*70)
        
        return {
            'cycle_results': results,
            'system_status': self.coordinator.get_system_status(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def run_parallel_backtest(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run parallel backtests with multiple agents
        """
        self.logger.info("⚡ Running parallel backtests with all agents...")
        
        cycle_data = {
            'market_data': market_data,
            'population_size': 10,  # Smaller per agent
            'strategies': []
        }
        
        # Get all backtest agents
        backtest_agents = [aid for aid, agent in self.coordinator.agents.items() 
                          if 'backtest' in aid]
        
        # Execute all in parallel
        result = await self.coordinator.execute_agents(cycle_data, backtest_agents)
        
        return result['results']
    
    def get_system_report(self) -> Dict[str, Any]:
        """Get comprehensive system report"""
        status = self.coordinator.get_system_status()
        
        return {
            'system_status': status,
            'agents_count': status['agents_count'],
            'agents_info': {
                aid: {
                    'name': agent.name,
                    'role': agent.role.value,
                    'status': agent.status.value,
                    'metrics': agent.metrics
                }
                for aid, agent in self.coordinator.agents.items()
            },
            'timestamp': datetime.now().isoformat()
        }
