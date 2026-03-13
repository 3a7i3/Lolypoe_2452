"""
Crypto AI Trading System V6
Autonomous AI-driven quantitative trading platform
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any

from core.market_scanner import MarketScanner
from core.orchestrator import Orchestrator
from core.portfolio_manager import PortfolioManager
from core.risk_engine import RiskEngine
from ai.strategy_selector import find_best_strategy
from quant.optimizer import optimize_portfolio
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)


class CryptoAISystem:
    """Main system coordinator"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.orchestrator = Orchestrator(self.config)
        self.portfolio_manager = PortfolioManager()
        self.risk_engine = RiskEngine()
        self.market_scanner = MarketScanner()
        self.running = False
        logger.info("✅ Crypto AI System V6 initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            'max_positions': 20,
            'max_drawdown': 0.25,
            'target_volatility': 0.15,
            'rebalance_frequency': 'daily',
            'strategy_iterations': 50,
            'enable_rl': True,
            'enable_genetic_algo': True,
        }
    
    async def run(self):
        """Main system loop"""
        self.running = True
        logger.info("🚀 Starting Crypto AI System...")
        
        while self.running:
            try:
                # 1. Scan market
                logger.info("📊 Scanning market...")
                market_data = await self.market_scanner.scan()
                
                # 2. Generate and evaluate strategies
                logger.info("🧠 Generating strategies...")
                strategies = await self.orchestrator.generate_strategies(market_data)
                
                # 3. Find best strategies
                logger.info("✅ Selecting best strategies...")
                best_strategies = await self.orchestrator.evaluate_strategies(strategies)
                
                # 4. Optimize portfolio
                logger.info("💼 Optimizing portfolio...")
                allocation = optimize_portfolio(best_strategies)
                
                # 5. Update positions
                logger.info("🎯 Updating positions...")
                await self.portfolio_manager.update_positions(allocation)
                
                # 6. Monitor risk
                risk_status = self.risk_engine.check_risks(self.portfolio_manager.get_portfolio())
                if not risk_status['safe']:
                    logger.warning(f"⚠️ Risk alert: {risk_status['alert']}")
                    await self.portfolio_manager.reduce_exposure(risk_status['reduction'])
                
                logger.info(f"✨ Cycle complete at {datetime.now()}")
                
                # Wait before next cycle
                await asyncio.sleep(self.config.get('cycle_interval', 300))
                
            except Exception as e:
                logger.error(f"❌ System error: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """Stop the system"""
        self.running = False
        logger.info("🛑 System stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'running': self.running,
            'portfolio': self.portfolio_manager.get_portfolio(),
            'risk_level': self.risk_engine.get_risk_level(),
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Main entry point"""
    system = CryptoAISystem()
    
    try:
        asyncio.run(system.run())
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        system.stop()


if __name__ == '__main__':
    main()
