from __future__ import annotations

import argparse
import os
import random
import time
from pathlib import Path

from agents.execution.arbitrage_agent import ArbitrageAgent
from agents.execution.execution_engine import ExecutionEngine
from agents.execution.liquidity_agent import LiquidityAnalyzer
from agents.execution.paper_trading_engine import PaperTradingEngine
from agents.market.market_scanner import MarketScanner
from agents.market.orderflow_agent import OrderFlowAnalyzer
from agents.market.regime_detector import RegimeDetector
from agents.market.volatility_agent import VolatilityDetector
from agents.monitoring.performance_monitor import PerformanceMonitor
from agents.monitoring.system_monitor import SystemMonitor
from agents.quant.backtest_lab import BacktestLab
from agents.quant.monte_carlo import MonteCarloSimulator
from agents.quant.portfolio_optimizer import PortfolioOptimizer
from agents.research.feature_engineer import FeatureEngineer
from agents.research.model_builder import ModelBuilder
from agents.research.paper_analyzer import PaperAnalyzer
from agents.research.strategy_researcher import StrategyResearcher
from agents.risk.drawdown_guard import DrawdownGuard
from agents.risk.exposure_manager import ExposureManager
from agents.risk.risk_monitor import RiskMonitor
from agents.strategy.genetic_optimizer import GeneticOptimizer
from agents.strategy.rl_trader import RLTrader
from agents.strategy.strategy_generator import StrategyGenerator
from dashboard.ai_dashboard import render_console_report
from data.market_database import MarketDatabase
from data.strategy_database import StrategyDatabase
from runtime_config import RuntimeConfig, get_env_int, load_runtime_config_from_env


def _get_env_int(name: str, default: int, min_value: int | None = None) -> int:
    """Backwards-compatible wrapper around runtime config integer parsing."""
    return get_env_int(name, default, min_value=min_value)


def run_system(
    max_cycles: int = 3,
    population_size: int = 300,
    sleep_seconds: int = 2,
    runtime: RuntimeConfig | None = None,
) -> None:
    os.chdir(Path(__file__).resolve().parent)

    cfg = runtime or RuntimeConfig(
        max_cycles=max_cycles,
        population_size=population_size,
        sleep_seconds=sleep_seconds,
    )
    random.seed(cfg.seed)

    scanner = MarketScanner()
    orderflow = OrderFlowAnalyzer()
    vol_detector = VolatilityDetector()
    regime_detector = RegimeDetector()

    strategy_generator = StrategyGenerator()
    optimizer = GeneticOptimizer()
    rl_trader = RLTrader()

    backtest_lab = BacktestLab()
    monte_carlo = MonteCarloSimulator()
    portfolio_opt = PortfolioOptimizer()

    paper_analyzer = PaperAnalyzer()
    feature_engineer = FeatureEngineer()
    strategy_researcher = StrategyResearcher()
    model_builder = ModelBuilder()

    risk_monitor = RiskMonitor(max_drawdown=cfg.max_drawdown)
    drawdown_guard = DrawdownGuard()
    exposure_manager = ExposureManager()

    execution = ExecutionEngine()
    arbitrage = ArbitrageAgent()
    liquidity = LiquidityAnalyzer()
    paper = PaperTradingEngine()

    perf_monitor = PerformanceMonitor()
    system_monitor = SystemMonitor()

    market_db = MarketDatabase()
    strategy_db = StrategyDatabase()

    cycle = 0
    while True:
        cycle += 1

        market = scanner.scan()
        candles = market["candles"]
        market_db.save_snapshot(market)

        symbols = [c["symbol"] for c in candles]
        close_prices = [float(c["close"]) for c in candles]
        features = feature_engineer.build(candles)
        vol = vol_detector.detect(close_prices)
        regime = regime_detector.detect(features["momentum"], vol)
        flow = orderflow.analyze(symbols)

        paper_analyzer.analyze(
            [
                {"title": "regime-adaptive trend", "novelty": random.uniform(0.5, 1.0), "relevance": random.uniform(0.4, 1.0)},
                {"title": "cross-exchange mean reversion", "novelty": random.uniform(0.5, 1.0), "relevance": random.uniform(0.4, 1.0)},
            ]
        )

        population = strategy_generator.generate_population(cfg.population_size)
        evolved = optimizer.evolve(population, generations=cfg.generations)
        results = [backtest_lab.run_backtest(strategy=s, data=candles) for s in evolved]
        ranked = strategy_researcher.rank(results)

        filtered = [r for r in ranked if risk_monitor.check(r)]
        top_results = filtered[:20] if filtered else ranked[:20]
        strategy_db.save_many(top_results)

        best = strategy_researcher.best(top_results)
        if best is None:
            print("No strategy candidates generated.")
            break

        portfolio_weights = portfolio_opt.optimize(top_results[:10])
        portfolio_weights = exposure_manager.cap(portfolio_weights, max_per_symbol=cfg.max_strategy_weight)

        bounded_vol = min(0.08, max(0.001, vol))
        mc = monte_carlo.simulate(
            mean_return=0.0005,
            volatility=bounded_vol,
            steps=cfg.monte_carlo_steps,
            paths=cfg.monte_carlo_paths,
        )
        model_info = model_builder.retrain(top_results)

        tradable = liquidity.filter_symbols(candles)
        symbol = tradable[0] if tradable else candles[0]["symbol"]
        action_state = f"{regime}:{'pos' if features['momentum'] > 0 else 'neg'}:{'buy' if flow[symbol] > 0 else 'sell'}"
        action = rl_trader.choose_action(action_state)

        dd = float(best.get("drawdown", 0.0))
        size = drawdown_guard.adjust_position_size(dd, base_size=1.0)
        price = next(float(c["close"]) for c in candles if c["symbol"] == symbol)

        # Arbitrage check can override action with a market-neutral SELL in this toy engine.
        if arbitrage.detect(price, price * random.uniform(0.985, 1.02), threshold=0.012):
            action = "SELL"

        order = execution.create_order(symbol=symbol, action=action, size=size)
        paper_state = paper.execute(order, mark_price=price)

        reward = float(best.get("sharpe", 0.0)) - float(best.get("drawdown", 0.0))
        next_state = f"{regime}:next"
        rl_trader.update(action_state, action, reward=reward, next_state=next_state)

        heartbeat = system_monitor.heartbeat(cycle)
        performance = perf_monitor.summarize(top_results)
        report = render_console_report(heartbeat, best, performance, portfolio_weights, model_info)

        if cycle % cfg.display_frequency == 0:
            print(report.strip())
            print(f"MonteCarlo: {mc} | Paper: {paper_state}")

        if cfg.max_cycles > 0 and cycle >= cfg.max_cycles:
            break
        time.sleep(max(0, cfg.sleep_seconds))


def _build_runtime_from_args() -> RuntimeConfig:
    parser = argparse.ArgumentParser(description="Run V9 legacy autonomous quant system")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print runtime config, then exit")
    parser.add_argument("--max-cycles", type=int, help="Override V9_MAX_CYCLES")
    parser.add_argument("--population", type=int, help="Override V9_POPULATION")
    parser.add_argument("--sleep-seconds", type=int, help="Override V9_SLEEP_SECONDS")
    args = parser.parse_args()

    cfg = load_runtime_config_from_env()
    if args.max_cycles is not None:
        cfg.max_cycles = max(0, args.max_cycles)
    if args.population is not None:
        cfg.population_size = max(1, args.population)
    if args.sleep_seconds is not None:
        cfg.sleep_seconds = max(0, args.sleep_seconds)
    if args.dry_run:
        cfg.dry_run = True

    return cfg


if __name__ == "__main__":
    runtime_cfg = _build_runtime_from_args()
    if runtime_cfg.dry_run:
        print("[DRY-RUN] Runtime configuration loaded:")
        for key, value in runtime_cfg.as_dict().items():
            print(f"  - {key}: {value}")
    else:
        run_system(runtime=runtime_cfg)
