"""
Crypto AI Trading System V7
Multi-Agent Architecture
Entry point for the new multi-agent system
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import numpy as np

from agents.coordinator import TradingMultiAgentSystem
from config import get_config, get_trading_symbols

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CryptoAITradingV7:
    """Multi-Agent Crypto AI Trading System V7"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize V7 system"""
        self.config = config or get_config()
        self.system = TradingMultiAgentSystem(self.config)
        
        # System state
        self.is_running = False
        self.cycle_count = 0
        self.start_time = None
        self.trading_symbols = get_trading_symbols()
        
        logger.info(f"✅ Crypto AI Trading System V7 initialized")
        logger.info(f"   Trading symbols: {len(self.trading_symbols)}")
    
    async def initialize(self, 
                        num_scanner_agents: int = 2,
                        num_strategy_agents: int = 5,
                        num_backtest_agents: int = 10,
                        num_risk_agents: int = 3):
        """Initialize agent pool"""
        logger.info("🤖 Initializing agent pool...")
        logger.info(f"   Scanners: {num_scanner_agents}")
        logger.info(f"   Generators: {num_strategy_agents}")
        logger.info(f"   Backtests: {num_backtest_agents}")
        logger.info(f"   Risk Managers: {num_risk_agents}")
        
        self.system.setup_agents(
            num_scanner_agents=num_scanner_agents,
            num_strategy_agents=num_strategy_agents,
            num_backtest_agents=num_backtest_agents,
            num_risk_agents=num_risk_agents
        )
        
        logger.info(f"✅ Agent pool ready ({num_scanner_agents + num_strategy_agents + num_backtest_agents + num_risk_agents + 2} agents)")
    
    def generate_mock_market_data(self) -> Dict[str, Any]:
        """Generate mock market data for demo"""
        market_data = {}
        
        for symbol in self.trading_symbols:
            # Generate realistic OHLCV data
            prices = 100 + np.cumsum(np.random.normal(0, 2, 100))
            volumes = np.random.normal(1000000, 200000, 100)
            
            market_data[symbol] = {
                'prices': prices.tolist(),
                'volumes': volumes.tolist(),
                'high': max(prices),
                'low': min(prices),
                'close': prices[-1],
                'volume': volumes[-1]
            }
        
        return market_data
    
    async def run(self, cycle_interval: int = 300, num_cycles: int = 10):
        """
        Main execution loop
        Args:
            cycle_interval: Seconds between cycles
            num_cycles: Number of cycles to run
        """
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("\n" + "🚀 "*35)
        logger.info("🚀 CRYPTO AI TRADING SYSTEM V7 - MULTI-AGENT MODE")
        logger.info("🚀 "*35 + "\n")
        
        try:
            for cycle in range(num_cycles):
                self.cycle_count += 1
                cycle_start = datetime.now()
                
                try:
                    logger.info(f"\n{'='*70}")
                    logger.info(f"🔄 CYCLE {self.cycle_count}/{num_cycles} - {cycle_start.strftime('%H:%M:%S')}")
                    logger.info(f"{'='*70}")
                    
                    # Generate market data
                    market_data = self.generate_mock_market_data()
                    logger.info(f"📊 Market Data: {len(market_data)} symbols loaded")
                    
                    # Execute trading cycle with agents
                    result = await self.system.run_trading_cycle(market_data)
                    
                    # Log results
                    cycle_results = result['cycle_results']
                    logger.info(f"\n📋 CYCLE RESULTS:")
                    for i, res in enumerate(cycle_results):
                        if isinstance(res, dict):
                            logger.info(f"   Agent {i}: {res.get('agent', 'Unknown')} → {str(res)[:60]}...")
                    
                    # Parallel backtests (optional)
                    if self.cycle_count % 3 == 0:
                        logger.info("\n⚡ Running parallel backtests...")
                        backtest_results = await self.system.run_parallel_backtest(market_data)
                        logger.info(f"   Parallel backtests: {len(backtest_results)} results")
                    
                    cycle_time = (datetime.now() - cycle_start).total_seconds()
                    logger.info(f"\n✅ Cycle completed in {cycle_time:.2f}s")
                    
                except Exception as e:
                    logger.error(f"❌ Cycle error: {str(e)}", exc_info=True)
                
                # Wait for next cycle
                if cycle < num_cycles - 1:
                    logger.info(f"⏳ Waiting {cycle_interval}s for next cycle...")
                    await asyncio.sleep(1)  # Short wait for demo
        
        except KeyboardInterrupt:
            logger.info("\n⛔ System interrupted by user")
        finally:
            self.is_running = False
            self._print_summary()
    
    def _print_summary(self):
        """Print system summary"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        logger.info("\n" + "="*70)
        logger.info("📊 SYSTEM SUMMARY")
        logger.info("="*70)
        
        report = self.system.get_system_report()
        
        logger.info(f"\n✅ System Performance:")
        logger.info(f"   Cycles Completed: {self.cycle_count}")
        logger.info(f"   Total Uptime: {uptime:.2f}s")
        logger.info(f"   Agents: {report['agents_count']}")
        
        # Agent metrics
        logger.info(f"\n🤖 Agent Metrics:")
        for agent_id, metrics in report['agents_info'].items():
            agent_metrics = metrics['metrics']
            logger.info(f"   {metrics['name']}:")
            logger.info(f"      Role: {metrics['role']}")
            logger.info(f"      Tasks Completed: {agent_metrics['tasks_completed']}")
            logger.info(f"      Messages Sent: {agent_metrics['messages_sent']}")
        
        logger.info("\n" + "="*70)
        logger.info("🌟 V7 Multi-Agent System Ready for Production")
        logger.info("="*70 + "\n")


# Demo: Parallel Agent Execution
async def demo_parallel_execution():
    """Demo parallel agent execution"""
    logger.info("\n" + "🎯 "*30)
    logger.info("🎯 DEMO: Parallel Agent Execution")
    logger.info("🎯 "*30 + "\n")
    
    system = CryptoAITradingV7()
    await system.initialize(
        num_scanner_agents=2,
        num_strategy_agents=5,
        num_backtest_agents=10,
        num_risk_agents=3
    )
    
    # Run 3 cycles for demo
    await system.run(cycle_interval=60, num_cycles=3)


# Entry point
if __name__ == '__main__':
    asyncio.run(demo_parallel_execution())
