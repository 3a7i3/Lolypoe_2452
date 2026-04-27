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
from agents.intelligence import FeatureEngineer
from agents.intelligence.regime_detector import AdvancedRegimeDetector
from agents.market.market_scanner import MarketScanner
from agents.market.orderflow_agent import OrderFlowAnalyzer
from agents.market.volatility_agent import VolatilityDetector
from agents.monitoring.prompt_doctor_agent import CreatePromptAgent
from agents.monitoring.performance_monitor import PerformanceMonitor
from agents.monitoring.system_monitor import SystemMonitor
from agents.portfolio import PortfolioBrain
from agents.quant.backtest_lab import BacktestLab
from agents.quant.monte_carlo import MonteCarloSimulator
from agents.quant.portfolio_optimizer import PortfolioOptimizer
from agents.research.feature_engineer import FeatureEngineer as LegacyFeatureEngineer
from agents.research.model_builder import ModelBuilder
from agents.research.paper_analyzer import PaperAnalyzer
from agents.research.strategy_researcher import StrategyResearcher
from agents.risk.drawdown_guard import DrawdownGuard
from agents.risk.exposure_manager import ExposureManager
from agents.risk.risk_monitor import RiskMonitor
from agents.strategy.genetic_optimizer import GeneticOptimizer
from agents.strategy.rl_trader import RLTrader
from agents.strategy.strategy_generator import StrategyGenerator
from agents.whales import WhaleRadar
from dashboard.control_center import AIControlCenter
from dashboard.director_dashboard import DirectorDashboard
from market_radar import MarketRadar
from strategy_factory import StrategyFactory
from ai_evolution.evolution_engine import EvolutionEngine
from liquidity_map import LiquidityFlowMap
from data.market_database import MarketDatabase
from data.strategy_database import StrategyDatabase
from databases.strategy_scoreboard import StrategyScoreboard
from engine.decision_engine import DecisionEngine, StrategyRanker
from runtime_config import RuntimeConfig, get_env_int, load_runtime_config_from_env


def _get_env_int(name: str, default: int, min_value: int | None = None) -> int:
    """Backwards-compatible wrapper around runtime config integer parsing."""
    return get_env_int(name, default, min_value=min_value)


def run_v91_system(
    max_cycles: int = 3,
    population_size: int = 300,
    sleep_seconds: int = 2,
    runtime: RuntimeConfig | None = None,
    enable_director: bool = False,
) -> None:
    """V9.1 - Autonomous Quant Lab with AI Portfolio Brain + Whale Radar + Intelligence Layer."""
    os.chdir(Path(__file__).resolve().parent)

    cfg = runtime or RuntimeConfig(
        max_cycles=max_cycles,
        population_size=population_size,
        sleep_seconds=sleep_seconds,
    )
    random.seed(cfg.seed)

    # ===== MARKET & INTELLIGENCE =====
    _ccxt_symbols = [s.strip() for s in cfg.ccxt_symbols.split(",") if s.strip()]
    scanner = MarketScanner(symbols=_ccxt_symbols, timeframe=cfg.ccxt_timeframe, cache_ttl=cfg.ccxt_cache_ttl)
    orderflow = OrderFlowAnalyzer()
    vol_detector = VolatilityDetector()
    feature_eng = FeatureEngineer()
    regime_detector = AdvancedRegimeDetector()

    # ===== WHALE RADAR =====
    whale_radar = WhaleRadar(threshold_usd=cfg.whale_threshold_usd)

    # ===== AI MARKET RADAR (NEW!) =====
    market_radar = MarketRadar(
        min_liquidity_usd=1_000.0,
        min_volume_usd=500.0,
        whale_threshold_usd=cfg.whale_threshold_usd,
    )

    # ===== STRATEGY GENERATION & EVOLUTION =====
    strategy_generator = StrategyGenerator()
    optimizer = GeneticOptimizer()
    rl_trader = RLTrader()
    strategy_factory = StrategyFactory()

    # ===== AI EVOLUTION ENGINE (NEW!) =====
    evolution_engine = EvolutionEngine(
        population_size=max(30, cfg.population_size // 5),
        memory_seed_ratio=0.3,
        generations=max(1, cfg.generations - 1),
    )

    # ===== LIQUIDITY FLOW MAP (NEW!) =====
    flow_map = LiquidityFlowMap(opportunity_threshold=40.0)

    # ===== QUANT LAB =====
    backtest_lab = BacktestLab()
    monte_carlo = MonteCarloSimulator()

    # ===== PORTFOLIO BRAIN (NEW!) =====
    portfolio_brain = PortfolioBrain()

    # ===== DECISION ENGINE (NEW!) =====
    decision_engine = DecisionEngine(
        min_sharpe=cfg.min_sharpe_for_trade,
        max_drawdown_for_trade=cfg.trade_max_drawdown,
        whale_block_threshold=cfg.whale_block_threshold,
    )
    ranker = StrategyRanker()

    # ===== TRADITIONAL AGENTS =====
    paper_analyzer = PaperAnalyzer()
    legacy_feature_eng = LegacyFeatureEngineer()
    strategy_researcher = StrategyResearcher()
    model_builder = ModelBuilder()

    # ===== RISK MANAGEMENT =====
    risk_monitor = RiskMonitor(max_drawdown=cfg.max_drawdown)
    drawdown_guard = DrawdownGuard()
    exposure_manager = ExposureManager()

    # ===== EXECUTION =====
    execution = ExecutionEngine()
    arbitrage = ArbitrageAgent()
    liquidity = LiquidityAnalyzer()
    paper = PaperTradingEngine()

    # ===== MONITORING =====
    perf_monitor = PerformanceMonitor()
    system_monitor = SystemMonitor()
    control_center = AIControlCenter()
    director = DirectorDashboard(starting_balance=100_000.0) if enable_director else None
    doctor_agent = CreatePromptAgent()

    # ===== DATABASES =====
    market_db = MarketDatabase()
    strategy_db = StrategyDatabase()
    scoreboard = StrategyScoreboard()

    cycle = 0
    _prev_doctor_health = 100.0  # track doctor health across cycles
    while True:
        cycle += 1
        print("\n🚀 Starting V9.1 Cycle...")

        # ===== 1. MARKET SCAN + INTELLIGENCE =====
        market = scanner.scan()
        candles = market["candles"]
        data_source = market["data_source"]
        market_db.save_snapshot(market)

        symbols = [c["symbol"] for c in candles]
        close_prices = [float(c["close"]) for c in candles]

        # Historique OHLCV réel pour le backtesting (symbole principal)
        primary_symbol = symbols[0] if symbols else _ccxt_symbols[0]
        history_candles = scanner.fetch_history(primary_symbol, limit=cfg.ccxt_history_limit)
        backtest_data = history_candles if len(history_candles) >= 2 else candles

        # Advanced feature engineering (sur l'historique si disponible)
        features = feature_eng.extract_features(history_candles if len(history_candles) >= 3 else candles)
        anomalies = feature_eng.detect_anomalies(features)

        # Regime detection
        regime = regime_detector.classify(features, close_prices)
        suggested_strategy_type = regime_detector.suggest_strategy_type(regime)

        # Whale scanning
        whale_data = []
        for c in candles:
            whale_scan = whale_radar.scan(c["symbol"], float(c["volume"]), float(c["close"]))
            whale_data.append(whale_scan)

        whale_alerts = [alert for w in whale_data for alert in w["alerts"]]

        # ===== 1b. AI MARKET RADAR (NEW!) =====
        radar_report = market_radar.sweep(candles, features, whale_alerts)
        radar_summary = radar_report.as_dict()
        if cycle % cfg.display_frequency == 0:
            top_opps = radar_report.top(3)
            opp_display = ", ".join(f"{o.symbol}({o.score:.0f})" for o in top_opps) or "none"
            print(f"📡 Market Radar: {radar_summary['opportunities_count']} opportunities | "
                  f"risk={radar_summary['risk_level']} | whale_flow={radar_summary['whale_flow']} | "
                  f"social={radar_summary['social_sentiment']:.2f} | top: {opp_display}")

        # ===== 2. STRATEGY GENERATION & EVOLUTION =====
        population = strategy_generator.generate_population(cfg.population_size)
        evolved = optimizer.evolve(population, generations=cfg.generations)

        # ===== 3. BACKTESTING LAB =====
        results = [backtest_lab.run_backtest(strategy=s, data=backtest_data) for s in evolved]

        # ===== 3b. AI STRATEGY FACTORY (NEW!) =====
        factory_report = strategy_factory.run(
            candles,
            target_count=max(30, min(120, cfg.population_size)),
            generations=max(1, cfg.generations - 1),
            regime=regime,
        )
        strategy_factory_summary = factory_report.as_dict()
        results.extend(factory_report.approved_results)

        if cycle % cfg.display_frequency == 0:
            print(
                f"🏭 Strategy Factory: gen={strategy_factory_summary['generated_count']} "
                f"bt={strategy_factory_summary['backtested_count']} "
                f"filt={strategy_factory_summary['filtered_count']} "
                f"approved={strategy_factory_summary['approved_count']} "
                f"blocked={strategy_factory_summary['blocked_count']} "
                f"mem_load={strategy_factory_summary.get('memory_loaded_count', 0)} "
                f"mem_save={strategy_factory_summary.get('memory_saved_count', 0)}"
            )

        # ===== 3c. AI EVOLUTION ENGINE (NEW!) =====
        evo_report = evolution_engine.run_cycle(
            cycle=cycle,
            regime=regime,
            candles=candles,
            doctor_health=_prev_doctor_health,
        )
        if cycle % cfg.display_frequency == 0:
            print(evolution_engine.render(evo_report))

        # ===== 3d. LIQUIDITY FLOW MAP (NEW!) =====
        flow_report = flow_map.analyze(
            candles=candles,
            whale_alerts=whale_alerts,
            regime=regime,
            cycle=cycle,
        )
        if cycle % cfg.display_frequency == 0:
            print(flow_map.render(flow_report))

        ranked = decision_engine.select_strategies(results, top_n=20)

        # ===== 4. STRATEGY SCOREBOARD (NEW!) =====
        for strategy_result in ranked[:10]:
            strategy = strategy_result.get("strategy")
            if strategy is not None:
                scoreboard.add(strategy, {**strategy_result, "cycle": cycle})

        scoreboard_stats = scoreboard.stats()

        # ===== 5. RISK FILTERING =====
        filtered = [r for r in ranked if risk_monitor.check(r)]
        top_results = filtered[:10] if filtered else ranked[:10]

        best = strategy_researcher.best(top_results)

        # ===== 6. AI PORTFOLIO BRAIN (NEW!) =====
        strategy_scores = [
            {
                "strategy_id": f"strat_{i}",
                "sharpe": float(r.get("sharpe", 0.0)),
                "drawdown": float(r.get("drawdown", 0.01)),
                "win_rate": float(r.get("win_rate", 0.5)),
            }
            for i, r in enumerate(top_results[:10])
        ]
        portfolio_allocation = portfolio_brain.compute_allocation(
            strategy_scores,
            features.get("realized_volatility", 0.02),
            max_strategy_weight=cfg.max_strategy_weight,
        )

        # ===== 7. DECISION ENGINE (NEW!) =====
        should_trade = decision_engine.should_trade(best, regime, whale_alerts)
        risk_limits = decision_engine.compute_risk_limits(
            features.get("realized_volatility", 0.02),
            max_risk=cfg.max_risk_per_trade,
        )

        # ===== 8. MODEL RETRAINING =====
        model_info = model_builder.retrain(top_results)

        # ===== 9. PAPER TRADING EXECUTION =====
        tradable = liquidity.filter_symbols(candles)
        symbol = tradable[0] if tradable else candles[0]["symbol"]
        action_state = f"{regime}:{'pos' if features['momentum'] > 0 else 'neg'}"
        action = rl_trader.choose_action(action_state)

        dd = float(best.get("drawdown", 0.0)) if best else 0.0
        size = drawdown_guard.adjust_position_size(dd, base_size=1.0)
        price = next(float(c["close"]) for c in candles if c["symbol"] == symbol)

        if arbitrage.detect(price, price * random.uniform(0.985, 1.02), threshold=0.012):
            action = "SELL"

        order = execution.create_order(symbol=symbol, action=action, size=size)
        paper_state = paper.execute(order, mark_price=price)

        # ===== 9b. DIRECTOR SUPER DASHBOARD UPDATE (NEW!) =====
        doctor_result_for_director = {
            "health_score": 100.0,
            "top_recommendation": "",
            "findings": [],
        }
        doctor_corrections_for_director: list[str] = []
        _prev_doctor_health = 100.0  # default; updated below if doctor runs

        if cfg.doctor_telegram_enabled:
            primary_allocation = next(iter(portfolio_allocation.values()), None)
            risk_level = "high" if dd > 0.10 else ("medium" if dd > 0.05 else "low")
            doctor_input = {
                "trade_signal": action,
                "allocation": primary_allocation,
                "risk_level": risk_level,
            }
            corrected_strategy, doctor_issues = doctor_agent.apply_doctor_corrections_with_issues(
                doctor_input,
            )
            doctor_corrections_for_director = doctor_issues
            _prev_doctor_health = max(0.0, 100.0 - len(doctor_issues) * 20.0)

            for issue in doctor_issues:
                doctor_message = f"[Bot Doctor ALERT] {issue} for user {cfg.doctor_telegram_user_id}"
                doctor_agent.send_telegram_message(cfg.doctor_telegram_user_id, doctor_message)

            if cfg.doctor_v26_report_enabled and cycle % cfg.display_frequency == 0:
                doctor_report = doctor_agent.build_v26_compatible_report(doctor_issues)
                print(f"[Bot Doctor V26 Report] {doctor_report}")
                if cfg.doctor_report_export_enabled:
                    exported_path = doctor_agent.export_v26_report(
                        report=doctor_report,
                        output_dir=cfg.doctor_report_export_dir,
                        cycle=cycle,
                    )
                    print(f"[Bot Doctor V26 Report] Exported JSON: {exported_path}")

            if cycle % cfg.display_frequency == 0:
                evolution = doctor_agent.build_evolution_snapshot(doctor_issues)
                print(f"[Bot Doctor Evolution] {evolution}")

            if cycle % cfg.display_frequency == 0:
                print(f"[Bot Doctor] Strategy snapshot after corrections: {corrected_strategy}")

        # ===== 9c. Director Dashboard update =====
        director_snapshot = None
        if director is not None:
            _whale_threat = max((w["threat_level"] for w in whale_data), default="low", key=str.lower)
            director_snapshot = director.update(
                cycle=cycle,
                market_regime=regime,
                whale_flow=_whale_threat,
                suggested_strategy_type=suggested_strategy_type,
                radar_summary=radar_summary,
                strategy_factory_summary=strategy_factory_summary,
                best_strategy=best,
                doctor_result=doctor_result_for_director,
                corrections=doctor_corrections_for_director,
                blocked_trade=not should_trade,
                paper_state=paper_state,
                trade_action=action,
                trade_symbol=symbol,
                trade_size=size,
                trade_price=price,
                evo_summary=evo_report.as_dict(),
                flow_summary=flow_report.as_dict(),
            )

        # ===== 10. MONITORING & CONTROL CENTER (NEW!) =====
        heartbeat = system_monitor.heartbeat(cycle)
        performance = perf_monitor.summarize(top_results)

        # Prepare control center data
        market_regime_data = {
            "regime": regime,
            "strategy_type": suggested_strategy_type,
            "momentum": features["momentum"],
            "realized_volatility": features["realized_volatility"],
            "anomalies": anomalies,
            "radar": radar_summary,
        }

        whale_radar_data = {
            "alerts": whale_alerts,
            "threat_level": max((w["threat_level"] for w in whale_data), default="low", key=str.lower),
        }

        decision_data = {
            "should_trade": should_trade,
            "reason": "High Sharpe + Low DD" if should_trade else "Market conditions unfavorable",
            "risk_limits": risk_limits,
        }

        health_data = {
            "status": "running",
            "agents_count": 20,
            "strategies_gen": len(evolved),
            "backtests_completed": len(results),
            "model_version": model_info.get("model_version", 1),
        }

        portfolio_brain_info = {
            "kelly_fraction": 0.25,
            "vol_target": features["realized_volatility"],
            "max_position": 0.3,
        }

        # Render control center
        data_source_info = {
            "data_source": data_source,
            "candle_count": len(candles),
            "history_count": len(backtest_data),
            "timeframe": cfg.ccxt_timeframe,
        }
        report = control_center.render_full_report(
            cycle,
            market_regime_data,
            whale_radar_data,
            best,
            scoreboard_stats,
            portfolio_allocation,
            portfolio_brain_info,
            decision_data,
            health_data,
            flow_data=flow_report.as_dict(),
            data_source_info=data_source_info,
        )

        if cycle % cfg.display_frequency == 0:
            print(report)
            if director is not None and director_snapshot is not None:
                print(director.render(director_snapshot))
        bounded_vol = min(0.08, max(0.001, features["realized_volatility"]))
        mc = monte_carlo.simulate(
            mean_return=0.0005,
            volatility=bounded_vol,
            steps=cfg.monte_carlo_steps,
            paths=cfg.monte_carlo_paths,
        )
        if cycle % cfg.display_frequency == 0:
            print(f"📊 MonteCarlo Results: {mc}")
            print(f"💰 Paper Trading State: {paper_state}")

        if cfg.max_cycles > 0 and cycle >= cfg.max_cycles:
            break

        time.sleep(max(0, cfg.sleep_seconds))


def _build_runtime_from_args() -> tuple[RuntimeConfig, bool, bool, bool]:
    parser = argparse.ArgumentParser(description="Run V9.1 autonomous quant system")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print runtime config, then exit")
    parser.add_argument(
        "--doctor-prompt-only",
        action="store_true",
        help="Print only the Bot Doctor prompt payload JSON, then exit",
    )
    parser.add_argument("--max-cycles", type=int, help="Override V9_MAX_CYCLES")
    parser.add_argument("--population", type=int, help="Override V9_POPULATION")
    parser.add_argument("--sleep-seconds", type=int, help="Override V9_SLEEP_SECONDS")
    parser.add_argument("--radar", action="store_true", help="Run a single Market Radar sweep and exit")
    parser.add_argument("--dashboard", action="store_true", help="Enable Director Super Dashboard output each cycle")
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
    if args.dashboard:
        cfg.director_dashboard_enabled = True

    return cfg, bool(args.doctor_prompt_only), bool(args.radar), bool(args.dashboard)


if __name__ == "__main__":
    runtime_cfg, doctor_prompt_only, radar_only, dashboard_mode = _build_runtime_from_args()
    if radar_only:
        from agents.market.market_scanner import MarketScanner as _Scanner
        from agents.intelligence import FeatureEngineer as _FE
        _scanner = _Scanner()
        _fe = _FE()
        _candles = _scanner.scan()["candles"]
        _features = _fe.extract_features(_candles)
        _radar = MarketRadar(whale_threshold_usd=runtime_cfg.whale_threshold_usd)
        _report = _radar.sweep(_candles, _features)
        print("\n📡 AI Market Radar — Single Sweep\n")
        for opp in _report.top(10):
            print(f"  {opp.symbol:20s}  score={opp.score:5.1f}  risk={opp.risk_level:6s}  "
                  f"whale={opp.whale_signal:14s}  flags={opp.flags}")
        print(f"\nSummary: {_report.as_dict()}")
    elif doctor_prompt_only:
        doctor_agent = CreatePromptAgent()
        print(doctor_agent.generate_prompt())
    elif runtime_cfg.dry_run:
        print("[DRY-RUN] Runtime configuration loaded:")
        for key, value in runtime_cfg.as_dict().items():
            print(f"  - {key}: {value}")

        print("\n[DRY-RUN] Bot Doctor Prompt Payload:")
        doctor_agent = CreatePromptAgent()
        print(doctor_agent.generate_prompt())
    else:
        run_v91_system(runtime=runtime_cfg, enable_director=dashboard_mode)
