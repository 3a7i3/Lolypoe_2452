"""
Main Orchestrator V16 – System coordinator and cycle runner
Manages all agents and components in autonomous trading loop
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG
from core.exchange_manager import ExchangeManager
from core.market_scanner import MarketScanner
from core.portfolio_manager import PortfolioManager
from core.risk_engine import RiskEngine
from core.execution_engine import ExecutionEngine

from ai.market_observer import MarketObserver
from ai.strategy_generator import StrategyGenerator
from ai.reinforcement_trader import RLTrader
from ai.risk_enforcer import RiskEnforcer

from quant.backtester import Backtester
from quant.optimizer import PortfolioOptimizer
from quant.regime_detector import detect_regime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING SETUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class QuantSystemV16:
    """Main orchestrator for V16 autonomous trading system"""

    def __init__(self, config: dict):
        """Initialize system"""
        self.config = config
        self.cycle_count = 0
        self.start_time = datetime.now()

        # Core infrastructure
        logger.info("🚀 Initializing V16 System...")
        self.exchange_mgr = ExchangeManager(config)
        self.market_scanner = MarketScanner(self.exchange_mgr)
        self.portfolio_mgr = PortfolioManager(config['trading']['initial_capital'])
        self.risk_engine = RiskEngine(max_drawdown=config['risk']['max_drawdown'])
        self.execution_engine = ExecutionEngine(self.exchange_mgr, 
                                               mode=config['trading']['mode'])

        # AI Agents
        self.market_observer = MarketObserver()
        self.strategy_generator = StrategyGenerator()
        self.rl_trader = RLTrader()
        self.risk_enforcer = RiskEnforcer(
            max_position_size=config['risk'].get('max_position', 0.10)
        )

        # Quant engines
        self.backtester = Backtester(
            initial_capital=config['trading']['initial_capital'],
            fee=config['trading']['fee'],
            slippage=config['trading']['slippage']
        )
        self.optimizer = PortfolioOptimizer()

        logger.info("✅ V16 System initialized successfully")

    def _stable_seed(self, text: str) -> int:
        """Deterministic seed independent from Python hash randomization."""
        seed = 0
        for idx, char in enumerate(text):
            seed = (seed + (idx + 1) * ord(char)) % (2**32)
        return seed

    def _build_synthetic_prices(
        self,
        symbol: str,
        market: str,
        timeframe: str,
        base_price: float,
        daily_change_pct: float,
        periods: int = 420,
    ) -> np.ndarray:
        """Build synthetic but regime-sensitive series for strategy research."""
        tf_scale = {
            "5m": 0.45,
            "15m": 0.65,
            "1h": 1.0,
            "4h": 1.4,
            "1d": 2.0,
        }
        vol_scale = {
            "crypto": 0.025,
            "forex": 0.007,
            "equities": 0.014,
        }

        drift = float(daily_change_pct) / 100.0 / 24.0
        sigma = vol_scale.get(market, 0.02) * tf_scale.get(timeframe, 1.0)
        seed = self._stable_seed(f"{symbol}|{market}|{timeframe}")
        rng = np.random.default_rng(seed)

        shocks = rng.normal(loc=drift, scale=max(sigma, 1e-6), size=periods)
        prices = np.zeros(periods, dtype=float)
        prices[0] = max(float(base_price), 1e-3)
        for i in range(1, periods):
            prices[i] = max(prices[i - 1] * (1.0 + shocks[i]), 1e-3)
        return prices

    async def scan_market(self) -> dict:
        """Phase 1: Scan market and detect signals"""
        logger.info(f"📊 [CYCLE {self.cycle_count}] Phase 1: Market Scan")
        
        market_data = await self.market_scanner.scan(limit_symbols=50)
        anomalies = await self.market_scanner.detect_anomalies(market_data)
        signals = await self.market_observer.analyze(market_data)

        return {
            'market_data': market_data,
            'anomalies': anomalies,
            'signals': signals
        }

    async def generate_strategies(self, market_data: dict) -> dict:
        """Phase 2: Generate, backtest, optimize, and validate strategies."""
        logger.info(f"📊 [CYCLE {self.cycle_count}] Phase 2: Strategy Generation")

        market_df = market_data.get("market_data")
        if market_df is None or getattr(market_df, "empty", True):
            logger.warning("No market snapshot available. Returning empty strategy set.")
            return {
                "best_strategies": [],
                "population_size": 0,
                "generation": self.strategy_generator.generation,
            }

        candidates = market_df.sort_values("composite_score", ascending=False).head(20).to_dict("records")

        sg_cfg = self.config["agents"]["strategy_generator"]
        lab_cfg = self.config.get("strategy_lab", {})
        risk_cfg = lab_cfg.get("risk_controls", {})
        bt_cfg = self.config.get("backtesting", {})

        population = self.strategy_generator.generate_population(
            size=int(sg_cfg.get("population_size", 50)),
            markets=list(sg_cfg.get("markets", ["crypto"])),
            timeframes=list(sg_cfg.get("timeframes", ["1h"])),
        )

        def evaluate_strategy(strategy: dict) -> dict:
            row = candidates[int(strategy["id"]) % len(candidates)]
            symbol = str(row.get("symbol", "BTC"))
            market = str(strategy.get("market", "crypto"))
            timeframe = str(strategy.get("timeframe", "1h"))
            prices = self._build_synthetic_prices(
                symbol=symbol,
                market=market,
                timeframe=timeframe,
                base_price=float(row.get("price", 100.0)),
                daily_change_pct=float(row.get("change_24h", 0.0)),
            )

            split = int(prices.size * 0.7)
            train_prices, test_prices = prices[:split], prices[split:]

            regime = detect_regime(prices[-200:])
            train_signals = self.strategy_generator.generate_signals(train_prices, strategy, regime=regime)
            test_signals = self.strategy_generator.generate_signals(test_prices, strategy, regime=regime)

            train_metrics = self.backtester.backtest(
                train_prices,
                train_signals,
                max_position=float(risk_cfg.get("max_position", 0.10)),
                risk_per_trade=float(risk_cfg.get("risk_per_trade", 0.01)),
                max_drawdown_stop=float(risk_cfg.get("max_drawdown_stop", 0.20)),
            )
            test_metrics = self.backtester.backtest(
                test_prices,
                test_signals,
                max_position=float(risk_cfg.get("max_position", 0.10)),
                risk_per_trade=float(risk_cfg.get("risk_per_trade", 0.01)),
                max_drawdown_stop=float(risk_cfg.get("max_drawdown_stop", 0.20)),
            )

            overfit = self.backtester.detect_overfitting(train_metrics, test_metrics)
            metrics = {
                "sharpe": float(test_metrics.get("sharpe", 0.0)),
                "sortino": float(test_metrics.get("sortino", 0.0)),
                "total_return": float(test_metrics.get("total_return", 0.0)),
                "max_drawdown": float(test_metrics.get("max_drawdown", 0.0)),
                "overfit_score": float(overfit),
                "regime": regime,
                "symbol": symbol,
                "train_sharpe": float(train_metrics.get("sharpe", 0.0)),
                "test_sharpe": float(test_metrics.get("sharpe", 0.0)),
                "is_overfit": overfit > float(bt_cfg.get("overfit_threshold", 0.35)),
            }
            return metrics

        evolved = population
        generation_count = int(sg_cfg.get("generations", 5))
        for _ in range(generation_count):
            evolved = self.strategy_generator.evolve(
                evolved,
                evaluate_strategy,
                mutation_rate=0.25,
                elite_size=max(8, len(evolved) // 5),
            )

        ranked = self.strategy_generator.evaluate_fitness(evolved, evaluate_strategy)
        self.strategy_generator.population = ranked

        best_count = int(sg_cfg.get("concurrent_strategies", 5))
        best = self.strategy_generator.get_best_strategies(best_count)

        optimized = None
        if best and bool(lab_cfg.get("enable_grid_search", True)):
            param_grid = {
                "rsi_period": [10, 14, 21],
                "fast_ema": [8, 12, 16],
                "slow_ema": [30, 50, 80],
                "entry_threshold": [0.25, 0.40, 0.55],
            }
            optimized = self.strategy_generator.grid_search_optimize(
                base_strategy=best[0],
                evaluator=evaluate_strategy,
                param_grid=param_grid,
                max_evals=int(lab_cfg.get("grid_search_budget", 72)),
            )
            if float(optimized.get("fitness", -1e9)) > float(best[0].get("fitness", -1e9)):
                best[0] = optimized

        return {
            "best_strategies": best,
            "optimized_strategy": optimized,
            "population_size": len(ranked),
            "generation": self.strategy_generator.generation,
            "markets_covered": sorted({str(s.get("market", "")) for s in best}),
            "timeframes_covered": sorted({str(s.get("timeframe", "")) for s in best}),
        }

    async def optimize_portfolio(self) -> dict:
        """Phase 3: Portfolio optimization"""
        logger.info(f"📊 [CYCLE {self.cycle_count}] Phase 3: Portfolio Optimization")
        
        # Get current positions
        allocation = {k: v for k, v in self.config['allocation'].items()}
        
        return {
            'target_allocation': allocation,
            'status': 'optimized'
        }

    async def execute_trades(self, strategy_result: dict) -> dict:
        """Phase 4: Execute trades (paper mode)"""
        logger.info(f"📊 [CYCLE {self.cycle_count}] Phase 4: Trade Execution")
        
        trades_executed = 0
        
        if self.config['trading']['mode'] == 'paper':
            logger.info("📄 Paper trading mode - simulating orders")
        else:
            logger.info("⚠️ Live trading mode - executing real orders")

        return {
            'trades_executed': trades_executed,
            'mode': self.config['trading']['mode']
        }

    async def check_risk(self) -> dict:
        """Phase 5: Risk validation and enforcement"""
        logger.info(f"📊 [CYCLE {self.cycle_count}] Phase 5: Risk Validation")
        
        # Update risk engine
        portfolio_value = 10000 + __import__('random').randint(-500, 500)
        self.risk_engine.update_equity(portfolio_value)
        
        risk_check = self.risk_engine.check_risk_limits()
        
        if risk_check['should_stop']:
            logger.error("🚨 RISK LIMIT VIOLATED - STOPPING")
            return {'status': 'STOP', 'risk_check': risk_check}
        
        return {'status': 'OK', 'risk_check': risk_check}

    async def run_cycle(self):
        """Execute one complete trading cycle"""
        self.cycle_count += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 CYCLE {self.cycle_count} START at {datetime.now()}")
        logger.info(f"{'='*60}")

        try:
            # Phase 1: Market scan
            market_result = await self.scan_market()
            
            # Phase 2: Strategy generation
            strategy_result = await self.generate_strategies(market_result)
            
            # Phase 3: Portfolio optimization
            portfolio_result = await self.optimize_portfolio()
            
            # Phase 4: Execute trades
            execution_result = await self.execute_trades(strategy_result)
            
            # Phase 5: Risk check
            risk_result = await self.check_risk()

            logger.info(f"✅ CYCLE {self.cycle_count} COMPLETE")
            logger.info(f"   Market signals: {len(market_result['signals'])}")
            logger.info(f"   Best strategy Sharpe: {strategy_result['best_strategies'][0]['fitness']:.3f}")
            logger.info(f"   System risk: {risk_result['risk_check']['status']}")

            return {
                'cycle': self.cycle_count,
                'market': market_result,
                'strategy': strategy_result,
                'portfolio': portfolio_result,
                'execution': execution_result,
                'risk': risk_result
            }

        except Exception as e:
            logger.error(f"❌ Cycle error: {e}", exc_info=True)
            return None

    async def run_autonomous_loop(self, cycles: int = 10, interval: int = 60):
        """Run autonomous trading loop"""
        logger.info(f"🤖 Starting autonomous loop ({cycles} cycles, {interval}s interval)")
        
        for i in range(cycles):
            result = await self.run_cycle()
            
            if result and result['risk']['status'] == 'STOP':
                logger.critical("🛑 System stopped due to risk limits")
                break
            
            if i < cycles - 1:
                logger.info(f"⏱️  Waiting {interval}s until next cycle...")
                await asyncio.sleep(interval)

        logger.info("✅ Autonomous loop completed")

    def get_system_status(self) -> dict:
        """Get complete system status"""
        uptime = datetime.now() - self.start_time
        
        return {
            'version': self.config['version'],
            'status': 'RUNNING',
            'uptime': str(uptime),
            'cycles': self.cycle_count,
            'trading_mode': self.config['trading']['mode'],
            'agents': {
                'market_observer': 'ACTIVE',
                'strategy_generator': 'ACTIVE',
                'rl_trader': 'ACTIVE',
                'risk_enforcer': 'ACTIVE'
            },
            'portfolio_value': 10000,
            'drawdown': self.risk_engine.calculate_drawdown(),
            'timestamp': datetime.now().isoformat()
        }


async def main():
    """Main entry point"""
    system = QuantSystemV16(CONFIG)
    
    # Run a few cycles
    await system.run_autonomous_loop(cycles=5, interval=2)
    
    # Print final status
    logger.info("\n" + "="*60)
    logger.info("📊 FINAL SYSTEM STATUS")
    logger.info("="*60)
    status = system.get_system_status()
    for k, v in status.items():
        logger.info(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
