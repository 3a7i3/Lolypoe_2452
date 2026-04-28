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
from agents.execution.live_paper_engine import LivePaperEngine
from agents.intelligence import FeatureEngineer
from agents.intelligence.regime_detector import AdvancedRegimeDetector
from agents.market.market_scanner import MarketScanner
from agents.market.orderflow_agent import OrderFlowAnalyzer
from agents.market.symbol_router import SymbolRouter
from agents.market.volatility_agent import VolatilityDetector
from agents.market.multi_timeframe import MultiTimeframeScanner
from agents.monitoring.prompt_doctor_agent import CreatePromptAgent
from agents.monitoring.performance_monitor import PerformanceMonitor
from agents.monitoring.system_monitor import SystemMonitor
from agents.notifications.telegram_notifier import TelegramNotifier
from agents.portfolio import PortfolioBrain
from agents.quant.backtest_lab import BacktestLab
from agents.quant.monte_carlo import MonteCarloSimulator
from agents.quant.portfolio_optimizer import PortfolioOptimizer
from agents.research.feature_engineer import FeatureEngineer as LegacyFeatureEngineer
from agents.research.model_builder import ModelBuilder
from agents.research.paper_analyzer import PaperAnalyzer
from agents.research.sentiment_feed import SentimentFeed
from agents.research.strategy_researcher import StrategyResearcher
from agents.risk.circuit_breaker import CircuitBreaker
from agents.risk.drawdown_guard import DrawdownGuard
from agents.risk.exposure_manager import ExposureManager
from agents.risk.kelly_criterion import KellyCriterion, compute_avg_win_loss
from agents.risk.cvar_calculator import CVaRCalculator
from agents.risk.risk_monitor import RiskMonitor
from agents.risk.stop_loss_manager import StopLossManager
from agents.quant.walk_forward import WalkForwardOptimizer
from agents.risk.position_sizer import PositionSizer
from agents.quant.regime_strategy_selector import RegimeStrategySelector
from agents.execution.portfolio_rebalancer import PortfolioRebalancer
from agents.reporting.html_reporter import HtmlReporter
from agents.simulation.historical_replay import HistoricalReplay
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
from databases.strategy_scoreboard_sql import StrategyScoreboardSQL
from engine.decision_engine import DecisionEngine, StrategyRanker
from runtime_config import RuntimeConfig, get_env_int, load_runtime_config_from_env
from agents.api.system_state import get_state


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
    _ccxt_exchanges = [e.strip() for e in cfg.ccxt_exchanges.split(",") if e.strip()]
    scanner = MarketScanner(
        symbols=_ccxt_symbols,
        timeframe=cfg.ccxt_timeframe,
        cache_ttl=cfg.ccxt_cache_ttl,
        exchanges=_ccxt_exchanges,
        cache_db_path=cfg.ccxt_cache_db or None,
        live_feed_interval=cfg.ccxt_ws_interval if cfg.ccxt_ws_enabled else 0.0,
        use_websocket=cfg.ccxt_ws_pro,
    )
    orderflow = OrderFlowAnalyzer()
    vol_detector = VolatilityDetector()
    feature_eng = FeatureEngineer()
    regime_detector = AdvancedRegimeDetector()

    # ===== MULTI-TIMEFRAME SCANNER (option AD) =====
    _mtf_timeframes = [tf.strip() for tf in cfg.mtf_timeframes.split(",") if tf.strip()]
    mtf_scanner: MultiTimeframeScanner | None = (
        MultiTimeframeScanner(
            base_scanner=scanner,
            timeframes=_mtf_timeframes,
            history_limit=cfg.ccxt_history_limit,
            min_alignment=cfg.mtf_min_alignment,
            sma_fast=cfg.mtf_sma_fast,
            sma_slow=cfg.mtf_sma_slow,
        )
        if cfg.mtf_enabled
        else None
    )

    # ===== TELEGRAM NOTIFIER (option H) =====
    notifier = TelegramNotifier(
        bot_token=cfg.telegram_bot_token,
        chat_id=cfg.telegram_chat_id,
        cooldown_seconds=cfg.telegram_cooldown,
    )

    # ===== KELLY CRITERION (option K) =====
    kelly = KellyCriterion(
        max_fraction=cfg.kelly_max_fraction,
        half_kelly=cfg.kelly_half,
    )

    # ===== CVaR / EXPECTED SHORTFALL (option M) =====
    cvar_calc = CVaRCalculator(
        confidence=cfg.cvar_confidence,
        max_loss=cfg.cvar_max_loss,
    )

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

    # Circuit Breakers (option P)
    circuit_breaker = CircuitBreaker(
        daily_loss_limit=cfg.cb_daily_loss_limit,
        drawdown_limit=cfg.cb_drawdown_limit,
        consecutive_losses=cfg.cb_consecutive_losses,
    )

    # ===== EXECUTION =====
    execution = ExecutionEngine()
    arbitrage = ArbitrageAgent()
    liquidity = LiquidityAnalyzer()
    paper = LivePaperEngine(initial_balance=cfg.initial_balance)  # option O

    # Symbol Router — multi-symbole parallèle (option Q)
    symbol_router = SymbolRouter(
        max_symbols=cfg.symbol_router_max,
        weighting=cfg.symbol_router_weighting,  # type: ignore[arg-type]
        min_volume=cfg.symbol_router_min_volume,
    )

    # Sentiment Feed — Fear & Greed (option R)
    sentiment_feed: SentimentFeed | None = (
        SentimentFeed(
            cache_ttl=cfg.sentiment_cache_ttl,
            fallback_score=cfg.sentiment_fallback_score,
        )
        if cfg.sentiment_enabled
        else None
    )

    # Stop Loss / Take Profit + Trailing (options S+T)
    sl_manager = StopLossManager(
        default_sl_pct=cfg.sl_pct,
        default_tp_pct=cfg.tp_pct,
        trailing_pct=cfg.sl_trailing_pct if cfg.sl_trailing_enabled else None,
    )

    # Walk-Forward Optimizer (option U)
    wfo = WalkForwardOptimizer(
        n_splits=cfg.wfo_n_splits,
        train_ratio=cfg.wfo_train_ratio,
    ) if cfg.wfo_enabled else None

    # Position Sizer adaptatif Kelly + CVaR (option V)
    sizer = PositionSizer(
        max_kelly_fraction=cfg.sizer_max_kelly,
        max_position_size=cfg.sizer_max_size,
        min_position_size=cfg.sizer_min_size,
        kelly_half=cfg.sizer_half_kelly,
        cvar_safety_factor=cfg.sizer_cvar_safety,
    )

    # Regime-Aware Strategy Selector (option W)
    regime_selector = RegimeStrategySelector(
        min_score=cfg.regime_selector_min_score,
    ) if cfg.regime_selector_enabled else None

    # Portfolio Rebalancer (option X)
    rebalancer = PortfolioRebalancer(
        drift_threshold=cfg.rebalancer_drift_threshold,
        max_orders=cfg.rebalancer_max_orders,
    ) if cfg.rebalancer_enabled else None

    # HTML Reporter (option Y)
    reporter = HtmlReporter(
        output_dir=cfg.report_output_dir,
        keep_last_n=cfg.report_keep_last,
    ) if cfg.report_enabled else None

    # ===== MONITORING =====
    perf_monitor = PerformanceMonitor()
    system_monitor = SystemMonitor()
    control_center = AIControlCenter()
    director = DirectorDashboard(starting_balance=100_000.0) if enable_director else None
    doctor_agent = CreatePromptAgent()

    # ===== DATABASES =====
    market_db = MarketDatabase()
    strategy_db = StrategyDatabase()
    scoreboard = StrategyScoreboardSQL(db_path=cfg.scoreboard_sql_path)

    # ===== API REST (option AE) =====
    _api_state = get_state()
    _api_state.update(
        max_cycles=cfg.max_cycles,
        config_snapshot=cfg.as_dict(),
        running=True,
        paused=False,
    )
    if cfg.api_enabled:
        import threading
        import uvicorn
        from agents.api.rest_api import build_app
        _api_app = build_app(state=_api_state)
        _api_thread = threading.Thread(
            target=uvicorn.run,
            args=(_api_app,),
            kwargs={"host": cfg.api_host, "port": cfg.api_port, "log_level": "warning"},
            daemon=True,
            name="v91-rest-api",
        )
        _api_thread.start()
        print(f"🌐 API REST démarrée → http://{cfg.api_host}:{cfg.api_port}/docs")

    if cfg.dashboard_live_enabled:
        from dashboard.live_dashboard import start_live_dashboard
        start_live_dashboard(
            host=cfg.api_host,
            port=cfg.dashboard_live_port,
            refresh_ms=cfg.dashboard_live_refresh_ms,
            state=_api_state,
        )
        print(f"📊 Dashboard live → http://{cfg.api_host}:{cfg.dashboard_live_port}")

    # ===== Alertes Slack/Discord (option AF) =====
    from agents.alerts.alert_engine import AlertEngine
    _alert_engine = AlertEngine(
        slack_url=cfg.alerts_slack_url,
        discord_url=cfg.alerts_discord_url,
        cooldown_s=cfg.alerts_cooldown_s,
        drawdown_warning_pct=cfg.alerts_drawdown_warning_pct,
        drawdown_critical_pct=cfg.alerts_drawdown_critical_pct,
        sharpe_improvement_threshold=cfg.alerts_sharpe_improvement,
        enabled=cfg.alerts_enabled,
    )

    # ===== Notification Email SMTP (option AL) =====
    if cfg.email_enabled:
        from agents.alerts.email_notifier import EmailNotifier, EmailConfig
        _email_notifier = EmailNotifier(EmailConfig(
            smtp_host=cfg.email_smtp_host,
            smtp_port=cfg.email_smtp_port,
            username=cfg.email_username,
            password=cfg.email_password,
            from_addr=cfg.email_from,
            to_addrs=[a.strip() for a in cfg.email_to.split(",") if a.strip()],
        ))
        _email_notifier.attach_to_alert_engine(_alert_engine)
        print(f"📧 Email SMTP activé → {cfg.email_to}")

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

        # ===== 1a. CHECK SL/TP/TRAILING (options S+T) avant tout le reste =====
        _price_map = {c["symbol"]: float(c["close"]) for c in candles}
        sl_triggers = sl_manager.check_all(_price_map)
        for _trigger in sl_triggers:
            _sl_icon = {"stop_loss": "🛑", "take_profit": "💰", "trailing_stop": "📉"}.get(
                _trigger.trigger_type or "", "⚠️"
            )
            if cycle % cfg.display_frequency == 0:
                print(
                    f"{_sl_icon} {(_trigger.trigger_type or '').upper()} déclenché "
                    f"sur {_trigger.symbol} @ {_trigger.current_price:.4f} "
                    f"(seuil={_trigger.trigger_price:.4f})"
                )
            # Force un SELL sur le symbole déclenché
            _sl_order = execution.create_order(
                symbol=_trigger.symbol, action="SELL", size=cfg.sl_pct
            )
            paper.execute(_sl_order, mark_price=_trigger.current_price, cycle=cycle)
            sl_manager.clear(_trigger.symbol)  # ferme le suivi SL

        symbols = [c["symbol"] for c in candles]
        close_prices = [float(c["close"]) for c in candles]

        # Historique OHLCV réel pour le backtesting (symbole principal)
        primary_symbol = symbols[0] if symbols else _ccxt_symbols[0]
        history_candles = scanner.fetch_history(primary_symbol, limit=cfg.ccxt_history_limit)
        backtest_data = history_candles if len(history_candles) >= 2 else candles

        # ===== Export Parquet OHLCV (option AJ) =====
        if cfg.parquet_enabled and len(history_candles) >= 2:
            try:
                from agents.data.parquet_exporter import ParquetExporter
                _pq_exp = ParquetExporter(
                    output_dir=cfg.parquet_output_dir,
                    compression=cfg.parquet_compression,
                )
                _raw_ohlcv = [
                    [
                        int(c.get("timestamp", 0)) if "timestamp" in c
                        else int(c.get("ts", 0)),
                        float(c.get("open", c.get("close", 0))),
                        float(c.get("high", c.get("close", 0))),
                        float(c.get("low", c.get("close", 0))),
                        float(c["close"]),
                        float(c.get("volume", 0.0)),
                    ]
                    for c in history_candles
                ]
                _sym_slash = primary_symbol.replace("USDT", "/USDT")
                _pq_meta = _pq_exp.save(
                    symbol=_sym_slash,
                    timeframe=cfg.ccxt_timeframe,
                    ohlcv=_raw_ohlcv,
                    append=cfg.parquet_append,
                )
                if cycle % cfg.display_frequency == 0:
                    print(
                        f"💾 Parquet sauvegardé : {_pq_meta.n_bars} barres "
                        f"→ {_pq_meta.file_path} ({_pq_meta.file_size_bytes // 1024} Ko)"
                    )
            except Exception as _pq_exc:
                print(f"[WARN] Parquet export échoué : {_pq_exc}")

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

        # ===== 2b. REGIME-AWARE STRATEGY SELECTION (option W) =====
        if regime_selector is not None and evolved:
            evolved = regime_selector.select(evolved, regime=regime, top_n=len(evolved))
            if cycle % cfg.display_frequency == 0:
                _w_summary = regime_selector.summary(evolved, regime)
                print(
                    f"🧭 RegimeSelector [{regime}] | trend={_w_summary['trend_following']} "
                    f"mean={_w_summary['mean_reversion']} unknown={_w_summary['unknown']} "
                    f"→ optimal={_w_summary['regime_optimal_family']}"
                )

        # ===== 3. BACKTESTING LAB =====
        results = [backtest_lab.run_backtest(strategy=s, data=backtest_data) for s in evolved]

        # Résumé backtest pour le Director Dashboard (option J)
        _bt_pnls = [r["pnl"] for r in results if r]
        _bt_sharpes = [r["sharpe"] for r in results if r]
        _bt_dds = [r["drawdown"] for r in results if r]
        _bt_data_mode = results[0].get("data_mode", "synthetic") if results else "synthetic"
        backtest_summary = {
            "strategy_count": len(results),
            "best_pnl": max(_bt_pnls, default=0.0),
            "best_sharpe": max(_bt_sharpes, default=0.0),
            "max_drawdown": max(_bt_dds, default=0.0),
            "data_mode": _bt_data_mode,
            "candles_count": len(backtest_data),
        }

        # ===== 3b. WALK-FORWARD VALIDATION (option U) =====
        wfo_result: dict = {"data_mode": "disabled", "mean_sharpe": 0.0, "stability": 0.0}
        if wfo is not None and results:
            # Évalue la meilleure stratégie en OOS
            _best_for_wfo = max(results, key=lambda r: r.get("sharpe", 0.0))
            wfo_result = wfo.run(strategy=_best_for_wfo.get("strategy", {}), data=backtest_data)
            _wfo_robust = wfo.is_robust(wfo_result)
            if cycle % cfg.display_frequency == 0:
                _wfo_icon = "✅" if _wfo_robust else "⚠️"
                print(
                    f"{_wfo_icon} WFO | splits={wfo_result['n_splits_used']} | "
                    f"mean_sharpe={wfo_result['mean_sharpe']:.3f} | "
                    f"stability={wfo_result['stability']:.1%} | "
                    f"{'ROBUSTE' if _wfo_robust else 'FRAGILE'}"
                )

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

        # ===== 7b. SENTIMENT FEED (option R) =====
        sentiment_score: int = 50
        sentiment_label: str = "Neutral"
        sentiment_source: str = "disabled"
        if sentiment_feed is not None:
            _sent = sentiment_feed.fetch()
            sentiment_score = _sent["score"]
            sentiment_label = _sent["label"]
            sentiment_source = _sent["source"]
            # Score < bearish_threshold → réduit la décision de trader
            if sentiment_score < cfg.sentiment_bearish_threshold and should_trade:
                should_trade = False
                if cycle % cfg.display_frequency == 0:
                    print(f"😨 Sentiment BEARISH ({sentiment_label} {sentiment_score}) — trade bloqué")

        # ===== 8. MODEL RETRAINING =====
        model_info = model_builder.retrain(top_results)

        # ===== 9. PAPER TRADING EXECUTION =====
        tradable = liquidity.filter_symbols(candles)
        symbol = tradable[0] if tradable else candles[0]["symbol"]
        action_state = f"{regime}:{'pos' if features['momentum'] > 0 else 'neg'}"
        action = rl_trader.choose_action(action_state)

        dd = float(best.get("drawdown", 0.0)) if best else 0.0

        # Kelly Criterion (option K) — taille de position depuis le meilleur backtest
        if best:
            _win_rate = float(best.get("win_rate", 0.0))
            _returns_for_kelly = backtest_data  # bougies historiques
            _avg_win, _avg_loss = compute_avg_win_loss(
                [float(c["close"]) / float(backtest_data[i]["close"]) - 1.0
                 for i, c in enumerate(backtest_data[1:], 1)]
                if len(backtest_data) >= 2 else []
            )
            kelly_fraction = kelly.compute_size(
                win_rate=_win_rate,
                avg_win=_avg_win,
                avg_loss=_avg_loss,
                fallback=cfg.max_risk_per_trade,
            )
        else:
            kelly_fraction = cfg.max_risk_per_trade

        size = drawdown_guard.adjust_position_size(dd, base_size=kelly_fraction)

        # CVaR / Expected Shortfall (option M) — gate de risque extrême
        _price_returns = (
            [float(c["close"]) / float(backtest_data[i]["close"]) - 1.0
             for i, c in enumerate(backtest_data[1:], 1)]
            if len(backtest_data) >= 2 else []
        )
        cvar_value = cvar_calc.compute(_price_returns)
        cvar_within_limit = cvar_calc.is_within_limit(_price_returns)
        if not cvar_within_limit:
            # CVaR dépasse le seuil → réduit la taille de moitié
            size = size * 0.5

        # ===== Position Sizer adaptatif Kelly + CVaR (option V) =====
        _paper_equity_for_sizer = paper_state_prev.get("equity", cfg.initial_balance) if "paper_state_prev" in dir() else cfg.initial_balance
        _paper_win_rate = paper_state_prev.get("win_rate", 0.5) if "paper_state_prev" in dir() else 0.5
        _paper_avg_win = paper_state_prev.get("avg_win", _avg_win if best else 0.0) if "paper_state_prev" in dir() else 0.0
        _paper_avg_loss = paper_state_prev.get("avg_loss", _avg_loss if best else 0.0) if "paper_state_prev" in dir() else 0.0
        _cvar_abs = abs(cvar_value) * _paper_equity_for_sizer  # CVaR en $ approx
        sizing_result = sizer.compute(
            win_rate=_paper_win_rate,
            avg_win=_paper_avg_win,
            avg_loss=_paper_avg_loss,
            cvar=_cvar_abs,
            portfolio_value=_paper_equity_for_sizer,
        )
        if sizing_result.size > 0 and action != "HOLD":
            size = sizing_result.size  # override avec position sizing adaptatif
        if cycle % cfg.display_frequency == 0:
            print(
                f"📏 PositionSizer | method={sizing_result.method} "
                f"kelly={sizing_result.kelly_f:.3f} capped={sizing_result.kelly_capped:.3f} "
                f"cvar_cap={sizing_result.cvar_cap:.3f} → size={sizing_result.size:.3f}"
            )

        price = next(float(c["close"]) for c in candles if c["symbol"] == symbol)

        if arbitrage.detect(price, price * random.uniform(0.985, 1.02), threshold=0.012):
            action = "SELL"

        # ===== 7c. MULTI-TIMEFRAME CONFIRMATION (option AD) =====
        if mtf_scanner is not None and action != "HOLD":
            mtf_result = mtf_scanner.analyze(primary_symbol)
            if cycle % cfg.display_frequency == 0:
                _mtf_sigs = " | ".join(
                    f"{s.timeframe}:{s.direction}" for s in mtf_result.signals
                )
                print(
                    f"⏱️  MTF [{primary_symbol}] composite={mtf_result.composite_signal} "
                    f"align={mtf_result.alignment_score:.0%} ({_mtf_sigs})"
                )
            if cfg.mtf_require_alignment and mtf_result.composite_signal != action:
                if cycle % cfg.display_frequency == 0:
                    print(
                        f"⛔ MTF bloque l'action {action} "
                        f"(composite={mtf_result.composite_signal}, "
                        f"align={mtf_result.alignment_score:.0%})"
                    )
                action = "HOLD"

        # ===== Circuit Breaker (option P) — gate avant exécution =====
        _paper_dd_pct = paper_state_prev.get("drawdown_pct", 0.0) if "paper_state_prev" in dir() else 0.0
        _paper_realized_pnl = paper_state_prev.get("realized_pnl", 0.0) if "paper_state_prev" in dir() else 0.0
        cb_triggered = circuit_breaker.is_triggered(
            current_drawdown_pct=_paper_dd_pct,
            realized_pnl_today=_paper_realized_pnl,
            initial_balance=cfg.initial_balance,
        )
        if cb_triggered:
            cb_reason = circuit_breaker.reason()
            if cycle % cfg.display_frequency == 0:
                print(f"🔴 CIRCUIT BREAKER déclenché — {cb_reason}")
            notifier.send_health_alert(
                health_score=0.0,
                recommendation=f"Circuit Breaker: {cb_reason}",
            )
            action = "HOLD"  # bloque le trade

        # ===== Symbol Router (option Q) — dispatch multi-symbole =====
        routed_orders = symbol_router.build_orders(candles, action=action, total_size=size)
        if not routed_orders:
            routed_orders = [{"symbol": symbol, "action": action, "size": size}]

        # Trade principal (premier symbole)
        primary_order_info = routed_orders[0]
        order = execution.create_order(
            symbol=primary_order_info["symbol"],
            action=primary_order_info["action"],
            size=primary_order_info["size"],
        )
        paper_state = paper.execute(order, mark_price=price, cycle=cycle)

        # Enregistre les niveaux SL/TP si BUY exécuté (options S+T)
        if primary_order_info["action"] == "BUY":
            _atr = features.get("realized_volatility", 0.02) * price  # ATR approx
            if cfg.sl_atr_enabled and _atr > 0:
                sl_manager.set_levels_atr(
                    symbol=primary_order_info["symbol"],
                    entry_price=price,
                    atr=_atr,
                    sl_multiplier=cfg.sl_atr_multiplier,
                    tp_multiplier=cfg.sl_tp_multiplier,
                    trailing_pct=cfg.sl_trailing_pct if cfg.sl_trailing_enabled else None,
                )
            else:
                sl_manager.set_levels(
                    symbol=primary_order_info["symbol"],
                    entry_price=price,
                    trailing_pct=cfg.sl_trailing_pct if cfg.sl_trailing_enabled else None,
                )

        # Enregistre le résultat pour le circuit breaker (pertes consécutives)
        circuit_breaker.record_trade_result(paper_state.get("last_trade_pnl", 0.0))
        paper_state_prev = paper_state  # mémorisé pour le prochain cycle

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

        # ===== 9a. TELEGRAM ALERTS (option H) =====
        notifier.send_signal(action=action, symbol=symbol, price=price, data_source=data_source)
        notifier.send_whale_alert(whale_alerts)
        if _prev_doctor_health < 50:
            notifier.send_health_alert(
                health_score=_prev_doctor_health,
                recommendation=doctor_result_for_director.get("top_recommendation", ""),
            )

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
                data_source=data_source,
                exchange_metrics_report=scanner.get_metrics_report() if hasattr(scanner, "get_metrics_report") else "",
                backtest_summary=backtest_summary,
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
            "kelly_fraction": round(kelly_fraction, 4),
            "cvar": round(cvar_value, 4),
            "cvar_within_limit": cvar_within_limit,
            "vol_target": features["realized_volatility"],
            "max_position": cfg.kelly_max_fraction,
            # Paper trading live (option O)
            "equity": paper_state.get("equity", cfg.initial_balance),
            "realized_pnl": paper_state.get("realized_pnl", 0.0),
            "total_return_pct": paper_state.get("total_return_pct", 0.0),
            "paper_drawdown_pct": paper_state.get("drawdown_pct", 0.0),
            "paper_win_rate": paper_state.get("win_rate", 0.0),
            "paper_trade_count": paper_state.get("trade_count", 0),
            # Circuit Breaker (option P)
            "circuit_breaker_triggered": cb_triggered,
            "circuit_breaker_reason": circuit_breaker.reason(),
            # Symbol Router (option Q)
            "routed_symbols": [o["symbol"] for o in routed_orders],
            # Sentiment (option R)
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "sentiment_source": sentiment_source,
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
            print(f"💰 Paper Trading | Equity: ${paper_state.get('equity', 0):,.2f} | "
                  f"PnL: ${paper_state.get('realized_pnl', 0):+.2f} | "
                  f"Return: {paper_state.get('total_return_pct', 0):+.2f}% | "
                  f"DD: {paper_state.get('drawdown_pct', 0):.2f}% | "
                  f"WinRate: {paper_state.get('win_rate', 0):.1%} | "
                  f"Trades: {paper_state.get('trade_count', 0)}")
            _cb_status = circuit_breaker.status()
            _cb_icon = "🔴" if _cb_status["triggered"] else "🟢"
            print(
                f"{_cb_icon} Circuit Breaker | "
                f"consec_losses={_cb_status['consecutive_losses']} | "
                f"triggers_today={_cb_status['triggers_today']} | "
                f"{'BLOQUÉ: ' + _cb_status['reason'] if _cb_status['triggered'] else 'OK'}"
            )
            _routed_str = ", ".join(o["symbol"] for o in routed_orders)
            print(f"🔀 Symbol Router ({len(routed_orders)} symbols) → {_routed_str}")
            if sentiment_feed is not None:
                _sent_icon = "😨" if sentiment_score < 40 else ("😊" if sentiment_score > 60 else "😐")
                print(
                    f"{_sent_icon} Sentiment | score={sentiment_score}/100 | "
                    f"{sentiment_label} | source={sentiment_source}"
                )

        if cfg.max_cycles > 0 and cycle >= cfg.max_cycles:
            # Générer le rapport HTML du dernier cycle avant de sortir
            if reporter is not None and cycle % cfg.report_frequency == 0:
                _report_path = reporter.generate(
                    paper_state=paper_state,
                    backtest_summary=backtest_summary,
                    wfo_result=wfo_result if "wfo_result" in dir() else {},
                    symbol=symbol,
                    cycle=cycle,
                )
                if cycle % cfg.display_frequency == 0:
                    print(f"📄 Rapport HTML → {_report_path}")
            break

        # ===== Auto-Rebalancing (option X) =====
        if rebalancer is not None and cycle % cfg.rebalancer_frequency == 0:
            _current_weights = {o["symbol"]: o["size"] for o in routed_orders}
            _target_weights = symbol_router.allocate(candles)
            _rebal_orders = rebalancer.compute_orders(
                current_weights=_current_weights,
                target_weights=_target_weights,
                equity=float(paper_state.get("equity", cfg.initial_balance)),
            )
            if _rebal_orders:
                if cycle % cfg.display_frequency == 0:
                    print(f"⚖️  Rebalancer | {len(_rebal_orders)} ordre(s)")
                for _ro in _rebal_orders:
                    _ro_price = _price_map.get(_ro.symbol, price)
                    _ro_order = execution.create_order(
                        symbol=_ro.symbol, action=_ro.action, size=abs(_ro.drift)
                    )
                    paper.execute(_ro_order, mark_price=_ro_price, cycle=cycle)

        # ===== HTML Reporter (option Y) =====
        if reporter is not None and cycle % cfg.report_frequency == 0:
            _report_path = reporter.generate(
                paper_state=paper_state,
                backtest_summary=backtest_summary,
                wfo_result=wfo_result if "wfo_result" in dir() else {},
                symbol=symbol,
                cycle=cycle,
            )
            if cycle % cfg.display_frequency == 0:
                print(f"📄 Rapport HTML → {_report_path}")

        time.sleep(max(0, cfg.sleep_seconds))

        # ===== Mise à jour SystemState pour l'API REST (option AE) =====
        if cfg.api_enabled or cfg.dashboard_live_enabled:
            import datetime as _dt
            _sb_top: list[dict] = []
            try:
                _sb_top = scoreboard.top(5)
            except Exception:
                pass
            _api_state.update(
                cycle=cycle,
                max_cycles=cfg.max_cycles,
                regime=regime if "regime" in dir() else "unknown",
                symbol=symbol if "symbol" in dir() else "",
                data_source=data_source if "data_source" in dir() else "synthetic",
                equity=float(paper_state.get("equity", cfg.initial_balance)),
                pnl=float(paper_state.get("realized_pnl", 0.0)),
                return_pct=float(paper_state.get("total_return_pct", 0.0)),
                drawdown_pct=float(paper_state.get("drawdown_pct", 0.0)),
                win_rate=float(paper_state.get("win_rate", 0.0)),
                trades_count=int(paper_state.get("trade_count", 0)),
                best_strategy_type=best.strategy_type if best else "",
                best_sharpe=float(best.sharpe) if best else 0.0,
                circuit_breaker_ok=not cb_triggered if "cb_triggered" in dir() else True,
                circuit_breaker_reason=cb_reason if "cb_reason" in dir() else "",
                scoreboard_top=_sb_top,
                last_updated=_dt.datetime.now(_dt.timezone.utc).isoformat(),
            )
            # Historique equity pour dashboard live (option AH)
            _api_state.push_equity_point(
                cycle=cycle,
                equity=float(paper_state.get("equity", cfg.initial_balance)),
                pnl=float(paper_state.get("realized_pnl", 0.0)),
                drawdown_pct=float(paper_state.get("drawdown_pct", 0.0)),
            )

        # ===== Alertes Slack/Discord (option AF) =====
        _dd_pct = float(paper_state.get("drawdown_pct", 0.0))
        _eq = float(paper_state.get("equity", cfg.initial_balance))
        _alert_engine.maybe_alert_drawdown(cycle=cycle, drawdown_pct=_dd_pct, equity=_eq)
        if "cb_triggered" in dir() and cb_triggered:
            _alert_engine.maybe_alert_circuit_breaker(
                cycle=cycle,
                reason=cb_reason if "cb_reason" in dir() else "inconnu",
                equity=_eq,
            )
        if best:
            _best_type = best.strategy_type if hasattr(best, "strategy_type") else best.get("strategy_type", "")
            _best_sharpe = float(best.sharpe) if hasattr(best, "sharpe") else float(best.get("sharpe", 0.0))
            _alert_engine.maybe_alert_new_best_strategy(
                cycle=cycle,
                strategy_type=_best_type,
                sharpe=_best_sharpe,
            )

        # ===== Backtester vectorisé numpy (option AI) =====
        if cfg.backtester_enabled and len(backtest_data) >= 32:
            try:
                from agents.backtest.vectorized_backtester import VectorizedBacktester, BacktestConfig
                import numpy as np
                _vbt = VectorizedBacktester()
                _ohlcv_arr = np.array([
                    [float(c.get("open", c["close"])), float(c.get("high", c["close"])),
                     float(c.get("low", c["close"])), float(c["close"]), float(c.get("volume", 0.0))]
                    for c in backtest_data
                ])
                _bt_cfg = BacktestConfig(
                    strategy=cfg.backtester_strategy,
                    fast=cfg.backtester_fast,
                    slow=cfg.backtester_slow,
                )
                _vbt_result = _vbt.run(_ohlcv_arr, _bt_cfg)
                if cycle % cfg.display_frequency == 0:
                    print(
                        f"🔬 Backtester [{cfg.backtester_strategy.upper()}] "
                        f"Sharpe={_vbt_result.sharpe:.3f} "
                        f"DD={_vbt_result.max_drawdown_pct:.1f}% "
                        f"WR={_vbt_result.win_rate:.1%} "
                        f"trades={_vbt_result.n_trades}"
                    )
            except Exception as _vbt_exc:
                print(f"[WARN] Backtester vectorisé échoué : {_vbt_exc}")

        # ===== Optimiseur hyperparamètres (option AK) =====
        if cfg.hyperopt_enabled and cycle % cfg.hyperopt_frequency == 0 and len(backtest_data) >= 50:
            try:
                from agents.backtest.vectorized_backtester import VectorizedBacktester
                from agents.optim.hyperopt import HyperOptimizer
                import numpy as np
                _hb_arr = np.array([
                    [float(c.get("open", c["close"])), float(c.get("high", c["close"])),
                     float(c.get("low", c["close"])), float(c["close"]), float(c.get("volume", 0.0))]
                    for c in backtest_data
                ])
                _hopt = HyperOptimizer(
                    backtester=VectorizedBacktester(),
                    ohlcv=_hb_arr,
                )
                _hopt_result = _hopt.random_search(
                    n_trials=cfg.hyperopt_n_trials,
                    strategy=cfg.hyperopt_strategy,
                    metric=cfg.hyperopt_metric,
                )
                if _hopt_result.best_params and cycle % cfg.display_frequency == 0:
                    print(
                        f"🎯 HyperOpt [{cfg.hyperopt_strategy.upper()}] "
                        f"best={_hopt_result.best_params} "
                        f"Sharpe={_hopt_result.best_sharpe:.3f} "
                        f"({_hopt_result.n_evaluated}/{cfg.hyperopt_n_trials} évalués en "
                        f"{_hopt_result.duration_s:.1f}s)"
                    )
            except Exception as _hopt_exc:
                print(f"[WARN] HyperOpt échoué : {_hopt_exc}")

        # ===== Pause loop (option AE) =====
        while (cfg.api_enabled or cfg.dashboard_live_enabled) and _api_state.is_paused():
            time.sleep(0.5)

    # Arrêt propre du live feed (option G)
    if hasattr(scanner, "stop"):
        scanner.stop()

    # Résumé final (option AF)
    _alert_engine.alert_loop_finished(
        total_cycles=cycle,
        equity=float(paper_state.get("equity", cfg.initial_balance)) if "paper_state" in dir() else cfg.initial_balance,
        pnl=float(paper_state.get("realized_pnl", 0.0)) if "paper_state" in dir() else 0.0,
        best_sharpe=(
            float(best.sharpe) if "best" in dir() and best and hasattr(best, "sharpe")
            else float(best.get("sharpe", 0.0)) if "best" in dir() and best and isinstance(best, dict)
            else 0.0
        ),
    )
    _alert_engine.flush(timeout_s=5.0)


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
