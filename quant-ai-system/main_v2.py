"""
Crypto AI Trading System V6
Main orchestrator for autonomous trading
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import components
from config import get_config, get_trading_symbols
from core.market_scanner import MarketScanner
from ai.strategy_generator import StrategyGenerator
from ai.strategy_evaluator import StrategyEvaluator
from ai.strategy_selector import StrategySelector
from ai.price_predictor import LSTMPredictor
from ai.reinforcement_agent import RLTradingAgent
from core.portfolio_manager import PortfolioManager
from core.risk_engine import RiskEngine
from core.execution_engine import ExecutionEngine
from quant.optimizer import GeneticAlgorithmOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CryptoAISystem:
    """Main orchestrator for autonomous crypto AI trading system V6"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the system
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or get_config()
        
        # Initialize components
        self.market_scanner = MarketScanner(
            min_volume_usd=self.config['scanner']['min_volume_usd'],
            max_symbols=self.config['scanner']['max_symbols']
        )
        
        self.strategy_generator = StrategyGenerator()
        self.strategy_evaluator = StrategyEvaluator()
        self.strategy_selector = StrategySelector()
        self.price_predictor = LSTMPredictor()
        self.rl_agent = RLTradingAgent()
        
        self.portfolio = PortfolioManager(
            initial_capital=self.config['portfolio']['initial_capital'],
            max_positions=self.config['portfolio']['max_positions'],
            max_position_size=self.config['portfolio']['max_position_size'],
            max_drawdown=self.config['portfolio']['max_drawdown']
        )
        
        self.risk_engine = RiskEngine(
            max_drawdown=self.config['risk']['max_drawdown'],
            max_daily_loss=self.config['risk']['max_daily_loss']
        )
        
        self.execution_engine = ExecutionEngine(
            commission_rate=self.config['execution'].get('commission_rate', 0.001)
        )
        
        self.optimizer = GeneticAlgorithmOptimizer(
            population_size=self.config['strategy']['population_size']
        )
        
        # System state
        self.is_running = False
        self.cycle_count = 0
        self.start_time = None
        self.trading_symbols = get_trading_symbols()
        
        logger.info(f"✅ CryptoAISystem V6 initialized with {len(self.trading_symbols)} symbols")
    
    async def run(self, cycle_interval: int = 300):
        """
        Main system execution loop
        Args:
            cycle_interval: Seconds between each system cycle
        """
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("🚀 CryptoAISystem V6 starting...")
        logger.info(f"   Configuration: Portfolio=${self.config['portfolio']['initial_capital']:,.0f}, Max Positions={self.config['portfolio']['max_positions']}")
        
        try:
            while self.is_running:
                self.cycle_count += 1
                cycle_start = datetime.now()
                
                try:
                    logger.info(f"\n{'='*70}")
                    logger.info(f"  CYCLE #{self.cycle_count} - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(f"{'='*70}")
                    
                    # Market scanning phase
                    logger.info("📊 [1/6] Market Scanning...")
                    opportunities = await self._scan_markets()
                    logger.info(f"   Found {len(opportunities)} opportunities")
                    
                    # Strategy generation phase
                    logger.info("🧬 [2/6] Generating Strategies...")
                    strategies = await self._generate_strategies()
                    logger.info(f"   Generated {len(strategies)} candidate strategies")
                    
                    # Strategy evaluation phase
                    logger.info("📈 [3/6] Evaluating Strategies...")
                    best_strategies = await self._evaluate_strategies(strategies)
                    if best_strategies:
                        logger.info(f"   Top strategy score: {best_strategies[0]['score']:.2f}")
                    
                    # Portfolio optimization phase
                    logger.info("⚖️  [4/6] Optimizing Portfolio...")
                    await self._optimize_portfolio(best_strategies)
                    
                    # Risk management phase
                    logger.info("🛡️  [5/6] Risk Management...")
                    risk_ok = await self._check_risk_limits()
                    logger.info(f"   Risk status: {'✅ OK' if risk_ok else '⚠️ WARNING'}")
                    
                    # Position update phase
                    logger.info("💼 [6/6] Updating Positions...")
                    portfolio_status = self.portfolio.get_status()
                    logger.info(f"   Portfolio: ${portfolio_status['total_value']:,.0f}, Positions: {portfolio_status['total_positions']}")
                    
                    cycle_time = (datetime.now() - cycle_start).total_seconds()
                    logger.info(f"\n✅ Cycle completed in {cycle_time:.2f}s")
                
                except Exception as e:
                    logger.error(f"❌ Error in cycle: {str(e)}", exc_info=True)
                
                # Wait for next cycle
                logger.info(f"⏳ Waiting {cycle_interval}s until next cycle...\n")
                await asyncio.sleep(cycle_interval)
        
        except KeyboardInterrupt:
            logger.info("\n⛔ System interrupted by user")
        finally:
            self.is_running = False
            logger.info("🛑 System stopped")
    
    async def _scan_markets(self) -> List[Dict[str, Any]]:
        """Scan for market opportunities"""
        # Generate mock market data
        mock_market_data = {}
        for symbol in self.trading_symbols:
            mock_market_data[symbol] = {
                'prices': [100 + i * 0.1 for i in range(100)],
                'volumes': [1000000 + i * 10000 for i in range(100)],
                'exchange': 'binance'
            }
        
        opportunities = self.market_scanner.scan_market(mock_market_data, limit=10)
        return opportunities
    
    async def _generate_strategies(self) -> List[Dict[str, Any]]:
        """Generate candidate strategies"""
        strategies = self.strategy_generator.generate_population(
            self.config['strategy']['population_size']
        )
        return strategies
    
    async def _evaluate_strategies(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate strategies and return best ones"""
        # Generate mock market data for backtesting
        mock_market_data = [100 + i * 0.1 for i in range(100)]
        
        try:
            results = self.strategy_evaluator.evaluate_population(strategies, mock_market_data)
            return results[:self.config['strategy']['top_k_strategies']]
        except Exception as e:
            logger.warning(f"Strategy evaluation error: {e}")
            return []
    
    async def _optimize_portfolio(self, strategies: List[Dict[str, Any]]):
        """Optimize portfolio allocation"""
        if not strategies:
            logger.warning("No strategies to optimize")
            return
        
        # Update portfolio with top strategies
        for i, strategy in enumerate(strategies):
            allocation_pct = 0.5 if i == 0 else 0.25
            logger.info(f"   Strategy {strategy['id']}: {allocation_pct:.1%} allocation")
    
    async def _check_risk_limits(self) -> bool:
        """Check risk management limits"""
        portfolio_status = self.portfolio.get_status()
        
        # Check if still operational
        if self.portfolio.check_max_drawdown():
            logger.info("   Max drawdown check: ✅ OK")
            return True
        else:
            logger.warning("   Max drawdown exceeded: ⚠️ WARNING")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        portfolio_status = self.portfolio.get_status()
        
        return {
            'status': 'RUNNING' if self.is_running else 'STOPPED',
            'cycles': self.cycle_count,
            'uptime_seconds': uptime,
            'portfolio_value': portfolio_status['total_value'],
            'portfolio_return': portfolio_status['portfolio_return'],
            'positions_open': portfolio_status['total_positions'],
            'winning_positions': portfolio_status['winning_positions'],
            'losing_positions': portfolio_status['losing_positions']
        }
    
    def stop(self):
        """Stop the system"""
        logger.info("Stopping system...")
        self.is_running = False


# Entry point
if __name__ == '__main__':
    system = CryptoAISystem()
    try:
        asyncio.run(system.run(cycle_interval=300))
    except KeyboardInterrupt:
        system.stop()
