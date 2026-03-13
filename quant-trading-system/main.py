"""
Professional Quant Trading System V5 - Main Entry Point
Orchestrates 1000+ crypto monitoring with AI, arbitrage, and portfolio management
"""

import asyncio
import logging
import sys
import signal
from datetime import datetime
from core.orchestrator import QuantTradingOrchestrator
from utils.logger import setup_logger
from utils.notifier import Notifier
import config

# Setup logging
logger = setup_logger(__name__)

class SystemManager:
    """Main system manager for V5 trading system"""
    
    def __init__(self):
        self.orchestrator = QuantTradingOrchestrator()
        self.notifier = Notifier()
        self.running = True
        self.cycle_count = 0
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Shutdown signal received ({signum})")
        self.running = False
        self.orchestrator.cleanup()
        sys.exit(0)
    
    async def run_trading_cycle(self):
        """Execute one complete trading cycle"""
        try:
            self.cycle_count += 1
            cycle_start = datetime.now()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Trading Cycle #{self.cycle_count} started at {cycle_start}")
            logger.info(f"{'='*60}")
            
            # 1. Scan market for 1000+ cryptos
            logger.info("📊 Step 1: Scanning market for 1000+ cryptocurrencies...")
            market_data = await self.orchestrator.scan_market()
            logger.info(f"✓ Scanned {len(market_data)} cryptocurrencies")
            
            # 2. Generate multi-strategy signals
            logger.info("🤖 Step 2: Generating multi-strategy signals...")
            signals = await self.orchestrator.generate_signals(market_data)
            logger.info(f"✓ Generated {len(signals)} trading signals")
            
            # 3. AI Price Predictions
            if config.AI_MODELS_ENABLED:
                logger.info("🧠 Step 3: Running AI price predictions...")
                predictions = await self.orchestrator.generate_predictions(market_data)
                logger.info(f"✓ Generated predictions for {len(predictions)} symbols")
            
            # 4. Detect arbitrage opportunities
            if config.ARBITRAGE_ENABLED:
                logger.info("⚡ Step 4: Detecting arbitrage opportunities...")
                arbitrage_signals = await self.orchestrator.detect_arbitrage(market_data)
                logger.info(f"✓ Found {len(arbitrage_signals)} arbitrage opportunities")
            
            # 5. Risk filtering
            logger.info("🛡️  Step 5: Filtering signals through risk engine...")
            valid_trades = await self.orchestrator.filter_signals(signals)
            logger.info(f"✓ {len(valid_trades)} signals passed risk checks")
            
            # 6. Portfolio optimization
            logger.info("💰 Step 6: Optimizing portfolio allocation...")
            optimized_portfolio = await self.orchestrator.optimize_portfolio(valid_trades)
            logger.info(f"✓ Optimized portfolio with {len(optimized_portfolio)} positions")
            
            # 7. Execute trades
            logger.info("⚙️  Step 7: Executing trades...")
            executed = await self.orchestrator.execute_trades(optimized_portfolio)
            logger.info(f"✓ Executed {len(executed)} trades")
            
            # 8. Monitor positions
            logger.info("👁️  Step 8: Monitoring positions...")
            positions = await self.orchestrator.monitor_positions()
            logger.info(f"✓ Monitoring {len(positions)} active positions")
            
            # 9. Update portfolio metrics
            logger.info("📈 Step 9: Updating portfolio metrics...")
            metrics = await self.orchestrator.update_portfolio_metrics()
            logger.info(f"✓ Portfolio P&L: {metrics.get('pnl', 0):.2f}%")
            
            # 10. Run risk analysis
            if config.MONTE_CARLO_SIMULATIONS > 0:
                logger.info("🎲 Step 10: Running Monte Carlo simulation...")
                risk_analysis = await self.orchestrator.run_monte_carlo()
                logger.info(f"✓ VaR (95%): {risk_analysis.get('var_95', 0):.2f}%")
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            logger.info(f"\n✅ Cycle completed in {cycle_duration:.2f} seconds")
            logger.info(f"{'='*60}\n")
            
            return {
                'cycle': self.cycle_count,
                'signals': len(signals),
                'trades': len(executed),
                'positions': len(positions),
                'duration': cycle_duration
            }
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)
            if self.notifier:
                await self.notifier.send_alert(f"Trading cycle error: {str(e)}")
            return None
    
    async def run_continuous(self):
        """Run system continuously"""
        logger.info(f"\n🚀 Starting Quant Trading System V5")
        logger.info(f"Version: {config.VERSION}")
        logger.info(f"Mode: {'PRODUCTION' if config.PRODUCTION_MODE else 'DEVELOPMENT'}")
        logger.info(f"Monitoring {config.CRYPTO_UNIVERSE_SIZE}+ cryptocurrencies")
        logger.info(f"Enabled Strategies: {', '.join(config.ENABLED_STRATEGIES)}")
        
        update_interval = config.DATA_UPDATE_INTERVAL
        
        try:
            while self.running:
                result = await self.run_trading_cycle()
                
                if result:
                    logger.info(f"Waiting {update_interval}s before next cycle...")
                    await asyncio.sleep(update_interval)
                else:
                    logger.warning(f"Cycle failed, retrying in 10s...")
                    await asyncio.sleep(10)
                    
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            self.orchestrator.cleanup()
            logger.info("System shutdown complete")
    
    async def run_backtest(self):
        """Run backtesting mode"""
        logger.info("🔄 Running in Backtest mode...")
        
        results = await self.orchestrator.backtest(
            start_date=config.BACKTEST_START_DATE,
            end_date=config.BACKTEST_END_DATE,
            initial_capital=config.BACKTEST_INITIAL_CAPITAL
        )
        
        logger.info(f"\n{'='*60}")
        logger.info("BACKTEST RESULTS")
        logger.info(f"{'='*60}")
        logger.info(f"Total Trades: {results.get('total_trades', 0)}")
        logger.info(f"Win Rate: {results.get('win_rate', 0):.2%}")
        logger.info(f"Total Return: {results.get('total_return', 0):.2%}")
        logger.info(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
        logger.info(f"Max Drawdown: {results.get('max_drawdown', 0):.2%}")
        logger.info(f"{'='*60}\n")
    
    async def run_optimization(self):
        """Run parameter optimization"""
        logger.info("⚙️  Running parameter optimization...")
        
        optimized_params = await self.orchestrator.optimize_parameters(
            num_iterations=config.WALK_FORWARD_WINDOW
        )
        
        logger.info(f"\n{'='*60}")
        logger.info("OPTIMIZATION RESULTS")
        logger.info(f"{'='*60}")
        logger.info(f"Optimized Parameters: {optimized_params}")
        logger.info(f"{'='*60}\n")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quant Trading System V5')
    parser.add_argument('--mode', choices=['live', 'backtest', 'optimize', 'dashboard'],
                       default='live', help='System mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI models')
    
    args = parser.parse_args()
    
    # Override config from args
    if args.debug:
        config.DEBUG_MODE = True
        config.LOG_LEVEL = 'DEBUG'
    if args.no_ai:
        config.AI_MODELS_ENABLED = False
    
    manager = SystemManager()
    
    if args.mode == 'live':
        await manager.run_continuous()
    elif args.mode == 'backtest':
        await manager.run_backtest()
    elif args.mode == 'optimize':
        await manager.run_optimization()
    elif args.mode == 'dashboard':
        logger.info("Starting dashboard mode...")
        from dashboard.dashboard import run_dashboard
        run_dashboard()


if __name__ == "__main__":
    asyncio.run(main())
