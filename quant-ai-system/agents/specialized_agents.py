"""
Market Scanner Agent
Specializes in market opportunity scanning and analysis
"""

from agents.base_agent import Agent, AgentRole, AgentStatus
from typing import Dict, List, Any
from datetime import datetime
import numpy as np


class MarketScannerAgent(Agent):
    """Scans markets for trading opportunities"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.MARKET_SCANNER, 
                        "MarketScanner_Agent")
        self.opportunities_found = []
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan market data for opportunities
        Args:
            data: Market data including prices, volumes, symbols
        Returns:
            Opportunities found
        """
        self.logger.info("📊 Starting market scan...")
        
        market_data = data.get('market_data', {})
        min_volume = data.get('min_volume_usd', 100000)
        
        opportunities = []
        
        for symbol, prices in market_data.items():
            # Calculate metrics
            if isinstance(prices, list) and len(prices) > 20:
                recent_prices = prices[-20:]
                
                # Price momentum
                short_ma = np.mean(recent_prices[-5:])
                long_ma = np.mean(recent_prices)
                momentum = (short_ma - long_ma) / long_ma
                
                # Volatility
                returns = np.diff(recent_prices) / recent_prices[:-1]
                volatility = np.std(returns)
                
                # Opportunity score
                score = (abs(momentum) * 50) + ((1 - volatility) * 50)
                
                if score > 30:  # Threshold
                    opportunity = {
                        'symbol': symbol,
                        'score': min(score, 100),
                        'momentum': momentum,
                        'volatility': volatility,
                        'current_price': recent_prices[-1],
                        'timestamp': datetime.now().isoformat()
                    }
                    opportunities.append(opportunity)
                    self.logger.info(f"🎯 Opportunity found: {symbol} (score: {score:.1f})")
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        self.opportunities_found = opportunities
        
        # Send to strategy generator agent
        self.send_message(
            receiver_id='strategy_generator_1',
            message_type='opportunities_found',
            payload={'opportunities': opportunities[:10]},  # Top 10
            priority=5
        )
        
        return {
            'agent': self.name,
            'opportunities_count': len(opportunities),
            'top_opportunities': opportunities[:5],
            'timestamp': datetime.now().isoformat()
        }


class StrategyGeneratorAgent(Agent):
    """Generates trading strategies from market opportunities"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.STRATEGY_GENERATOR,
                        "StrategyGenerator_Agent")
        self.generated_strategies = []
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading strategies"""
        self.logger.info("🧬 Generating strategies...")
        
        opportunities = data.get('opportunities', [])
        population_size = data.get('population_size', 50)
        
        strategies = []
        
        # Generate strategies based on opportunities
        for i in range(population_size):
            strategy = {
                'id': f'STRAT_{i:05d}',
                'indicators': self._select_indicators(i),
                'entry_logic': f'Custom entry {i}',
                'exit_logic': f'Custom exit {i}',
                'timeframe': np.random.choice(['5m', '15m', '1h', '4h']),
                'risk_reward_ratio': np.random.uniform(1.5, 3.0),
                'generated_at': datetime.now().isoformat()
            }
            strategies.append(strategy)
        
        self.generated_strategies = strategies
        self.logger.info(f"✅ Generated {len(strategies)} strategies")
        
        # Send to backtester agent
        self.send_message(
            receiver_id='backtester_1',
            message_type='strategies_generated',
            payload={'strategies': strategies},
            priority=4
        )
        
        return {
            'agent': self.name,
            'strategies_count': len(strategies),
            'timestamp': datetime.now().isoformat()
        }
    
    def _select_indicators(self, seed: int) -> List[str]:
        """Select random indicators"""
        indicators = ['RSI', 'MACD', 'Bollinger', 'SMA', 'EMA', 'ATR', 'ADX']
        np.random.seed(seed)
        return list(np.random.choice(indicators, size=np.random.randint(2, 4), replace=False))


class BacktesterAgent(Agent):
    """Backtests and evaluates strategies"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.BACKTESTER,
                        "Backtester_Agent")
        self.backtest_results = []
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Backtest strategies"""
        self.logger.info("📈 Backtesting strategies...")
        
        strategies = data.get('strategies', [])
        
        results = []
        for strat in strategies:
            # Simulate backtest
            result = {
                'strategy_id': strat['id'],
                'total_return': np.random.uniform(5, 50),
                'sharpe_ratio': np.random.uniform(0.5, 3.0),
                'win_rate': np.random.uniform(0.45, 0.75),
                'max_drawdown': np.random.uniform(-0.25, -0.05),
                'profit_factor': np.random.uniform(1.0, 3.0),
                'num_trades': np.random.randint(10, 100),
                'score': 0
            }
            
            # Calculate composite score
            result['score'] = (
                result['total_return'] * 20 +
                result['sharpe_ratio'] * 5 +
                result['win_rate'] * 10 +
                (1 + result['max_drawdown']) * 15 +
                min(result['profit_factor'], 5) * 5
            )
            
            results.append(result)
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        self.backtest_results = results
        
        self.logger.info(f"✅ Backtested {len(results)} strategies")
        self.logger.info(f"   Top score: {results[0]['score']:.2f}" if results else "No results")
        
        # Send to risk manager
        self.send_message(
            receiver_id='risk_manager_1',
            message_type='backtest_results',
            payload={'results': results[:10]},  # Top 10
            priority=4
        )
        
        return {
            'agent': self.name,
            'backtest_count': len(results),
            'best_score': results[0]['score'] if results else 0,
            'timestamp': datetime.now().isoformat()
        }


class RiskManagerAgent(Agent):
    """Manages risk for strategies and portfolio"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.RISK_MANAGER,
                        "RiskManager_Agent")
        self.risk_assessments = []
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk"""
        self.logger.info("🛡️ Assessing risk...")
        
        strategies = data.get('strategies', [])
        portfolio_value = data.get('portfolio_value', 100000)
        max_drawdown = data.get('max_drawdown', 0.25)
        
        approved_strategies = []
        
        for strat in strategies:
            risk_score = strat.get('max_drawdown', -0.15)
            
            # Risk check
            if abs(risk_score) <= max_drawdown:
                strat['risk_approved'] = True
                strat['max_position_size'] = 0.1
                approved_strategies.append(strat)
                self.logger.info(f"✅ {strat['strategy_id']}: Risk approved")
            else:
                strat['risk_approved'] = False
                self.logger.warning(f"⚠️ {strat['strategy_id']}: Risk rejected")
        
        self.risk_assessments = approved_strategies
        
        # Send to portfolio optimizer
        self.send_message(
            receiver_id='portfolio_optimizer_1',
            message_type='risk_approved_strategies',
            payload={'strategies': approved_strategies},
            priority=3
        )
        
        return {
            'agent': self.name,
            'approved_count': len(approved_strategies),
            'rejected_count': len(strategies) - len(approved_strategies),
            'timestamp': datetime.now().isoformat()
        }


class PortfolioOptimizerAgent(Agent):
    """Optimizes portfolio allocation"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.PORTFOLIO_OPTIMIZER,
                        "PortfolioOptimizer_Agent")
        self.allocations = {}
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize portfolio"""
        self.logger.info("⚖️ Optimizing portfolio allocation...")
        
        strategies = data.get('strategies', [])
        portfolio_value = data.get('portfolio_value', 100000)
        max_positions = data.get('max_positions', 20)
        
        # Kelly Criterion allocation
        allocations = {}
        
        for i, strat in enumerate(strategies[:max_positions]):
            win_rate = strat.get('win_rate', 0.5)
            profit_factor = strat.get('profit_factor', 1.0)
            
            if profit_factor > 0:
                kelly = (win_rate * profit_factor - (1 - win_rate)) / profit_factor
                kelly = max(0.01, min(kelly * 0.5, 0.1))  # Safety adjustments
                
                allocations[strat['strategy_id']] = {
                    'allocation_pct': kelly,
                    'position_size': kelly * portfolio_value,
                    'risk_per_trade': kelly * 0.02
                }
        
        self.allocations = allocations
        self.logger.info(f"✅ Portfolio optimized: {len(allocations)} positions")
        
        # Send to execution agent
        self.send_message(
            receiver_id='execution_1',
            message_type='portfolio_allocation',
            payload={'allocations': allocations},
            priority=5
        )
        
        return {
            'agent': self.name,
            'positions_allocated': len(allocations),
            'total_allocation': sum(a['allocation_pct'] for a in allocations.values()),
            'timestamp': datetime.now().isoformat()
        }


class ExecutionAgent(Agent):
    """Executes trades based on portfolio allocation"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentRole.EXECUTION,
                        "Execution_Agent")
        self.executed_trades = []
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trades"""
        self.logger.info("💼 Executing trades...")
        
        allocations = data.get('allocations', {})
        
        trades = []
        for strategy_id, allocation in allocations.items():
            trade = {
                'strategy_id': strategy_id,
                'status': 'EXECUTED',
                'position_size': allocation['position_size'],
                'timestamp': datetime.now().isoformat()
            }
            trades.append(trade)
            self.logger.info(f"✅ Trade executed: {strategy_id}")
        
        self.executed_trades = trades
        
        return {
            'agent': self.name,
            'trades_executed': len(trades),
            'timestamp': datetime.now().isoformat()
        }
