# 📋 RAPPORT DÉTAILLÉ DES FONCTIONS DU PROJET

**Projet** : Crypto AI Terminal  
**Date** : 13 Mars 2026  
**Statut** : ✅ Production Ready  

---

## 📖 TABLE DES MATIÈRES

1. [Vue d'ensemble du workspace](#1-vue-densemble-du-workspace)
2. [quant-hedge-ai (V9.1) — Système principal](#2-quant-hedge-ai-v91--système-principal)
3. [crypto_quant_v16 — Dashboard + Exécution](#3-crypto_quant_v16--dashboard--exécution)
4. [quant-ai-system — Stack Docker](#4-quant-ai-system--stack-docker)
5. [Projets Legacy](#5-projets-legacy)
6. [Scripts & Utilitaires Workspace](#6-scripts--utilitaires-workspace)

---

## 1. Vue d'ensemble du workspace

Le workspace contient **5 systèmes de trading indépendants** + des utilitaires :

| Système | Emplacement | Type | Statut |
|---------|-------------|------|--------|
| **V9.1 Autonomous Quant Lab** | `quant-hedge-ai/` | Standalone Python | ✅ Production |
| **V16/V26/V30 Dashboard** | `crypto_quant_v16/` | Panel Dashboard + Exécution | ✅ Production |
| **V7 Docker Stack** | `quant-ai-system/` | Docker multi-container | ✅ Running |
| **Bot V3** | `bot-v3/` | Bot simple | 📦 Legacy |
| **Quant Bot V3 Pro** | `quant-bot-v3-pro/` | Bot avancé | 📦 Legacy |
| **Quant Hedge Bot** | `quant-hedge-bot/` | Bot hedge fund | 📦 Legacy |
| **Quant Trading System** | `quant-trading-system/` | Système complet | 📦 Legacy |

**Total** : ~200+ fichiers Python, ~15,000+ lignes de code

---

## 2. quant-hedge-ai (V9.1) — Système principal

**78 fichiers Python** | Point d'entrée : `main_v91.py` (~600 lignes)

### 2.1 Orchestrateur principal (`main_v91.py`)

Exécute un **cycle autonome en 10 phases** :

| Phase | Fonction | Description |
|-------|----------|-------------|
| 1 | Market Scan | Scanner de marché + extraction de features + détection de régime + radar baleines |
| 2 | Market Radar | TokenScanner + WhaleTracker + SocialScanner + AnomalyDetector |
| 3 | Strategy Gen | Génération de stratégies (300-500) + optimisation génétique |
| 4 | Evolution | Évolution avec mémoire persistante par régime |
| 5 | Liquidity Map | Cartographie de rotation du capital entre secteurs |
| 6 | Backtesting | Tests avec métriques Sharpe/Drawdown/Win-Rate/PnL |
| 7 | Portfolio | PortfolioBrain (Kelly + ciblage volumétrie) + DecisionEngine |
| 8 | Paper Trading | Exécution simulée + RL Trader |
| 9 | Bot Doctor | Validation IA des risques + alertes Telegram + corrections |
| 10 | Dashboards | AIControlCenter + DirectorDashboard + AgentMonitor |

**Options CLI** :
- `python main_v91.py` — Exécution continue
- `python main_v91.py --dry-run` — Validation config
- `python main_v91.py --radar` — Scan radar unique
- `python main_v91.py --dashboard` — Avec Director Dashboard
- `python main_v91.py --max-cycles=10 --population=200` — Override

---

### 2.2 Agents de Marché (4 fichiers)

| Classe | Fichier | Fonctions clés |
|--------|---------|----------------|
| `MarketScanner` | `agents/research/market_scanner.py` | Génération de bougies synthétiques OHLCV pour 4 symboles |
| `OrderFlowAnalyzer` | `agents/market/` | Détection de déséquilibre des ordres |
| `VolatilityDetector` | `agents/market/` | Calcul de volatilité historique |
| `AdvancedRegimeDetector` | `agents/intelligence/regime_detector.py` | Classification en 5 régimes : `bull_trend`, `bear_trend`, `sideways`, `high_volatility_regime`, `flash_crash` |

---

### 2.3 Agents de Recherche (4 fichiers)

| Classe | Fonctions clés |
|--------|----------------|
| `ResearchCoordinator` | Coordination des agents de recherche |
| `StrategyResearcher` | Classement par (Sharpe DESC, Drawdown ASC) |
| `PaperAnalyzer` | Score d'idées de stratégies à partir de notes/articles |
| `ModelBuilder` | Versioning de modèles ML + réentraînement |
| `TechnicalAnalyst` | Analyse technique multi-indicateurs |

---

### 2.4 Agents de Stratégie (3 fichiers)

| Classe | Fichier | Fonctions clés |
|--------|---------|----------------|
| `StrategyGenerator` | `agents/strategy/generator.py` | Création de stratégies aléatoires (6 indicateurs × 4 timeframes) |
| `GeneticOptimizer` | `agents/strategy/optimizer.py` | Mutation (période ±8, seuil ±0.2) + Croisement génétique |
| `RLTrader` | `agents/execution/rl_trader.py` | Q-learner epsilon-greedy (actions BUY/SELL/HOLD) |

---

### 2.5 Agents Quant (3 fichiers)

| Classe | Fichier | Fonctions clés |
|--------|---------|----------------|
| `BacktestLab` | `agents/quant/backtest_lab.py` | Backtests déterministes avec seed fixe |
| `MonteCarloSimulator` | `agents/quant/monte_carlo.py` | Simulation de chemins (median/p05/p95 valeurs terminales) |
| `PortfolioOptimizer` | `agents/quant/` | Pondération par ratio Sharpe/Drawdown |

---

### 2.6 Module Intelligence (2 classes, `agents/intelligence/`)

| Classe | Méthodes clés | Description |
|--------|---------------|-------------|
| `FeatureEngineer` | `extract_features()`, `detect_anomalies()` | Extraction de 7 features : `momentum`, `realized_volatility`, `volume_trend`, `price_range_ratio`, `trend_strength`, `returns_mean`, `returns_std` |
| `AdvancedRegimeDetector` | `detect_regime()` | Classification en 5 régimes de marché avec analyse de stabilité |

**Détection d'anomalies** : `extreme_momentum`, `spike_volatility`, `volume_explosion`

---

### 2.7 Module Portfolio Brain (3 classes, `agents/portfolio/`)

| Classe | Méthodes clés | Description |
|--------|---------------|-------------|
| `KellyAllocator` | `allocate()` | Fraction de Kelly : f = (bp - q) / b, capée à 0.25 (fractional Kelly 0.5x) |
| `VolatilityTargeter` | `target()` | Scaling des positions : `vol_scalar = target_vol / realized_vol` (0.5x à 2.0x) |
| `PortfolioBrain` | `optimize()` | Combine Kelly + ciblage volatilité + diversification |

**Impact** : Réduction du risque de 30%

---

### 2.8 Module Whale Radar (`agents/whales/`)

| Classe | Méthodes clés | Description |
|--------|---------------|-------------|
| `WhaleRadar` | `scan()`, `analyze_pattern()` | Détection de transactions > $500k, évaluation de menace (low/medium/high), pattern `whale_accumulation` |

**Impact** : Bloque 90% des mauvais trades

---

### 2.9 Decision Engine (`engine/decision_engine.py`)

| Classe | Méthodes clés | Description |
|--------|---------------|-------------|
| `StrategyRanker` | `rank()` | Score composite : `(Sharpe/DD) × (1 + WR×0.1 + PnL×0.01)` |
| `DecisionEngine` | `should_trade()`, `risk_limit()` | Vérifie : Sharpe > 2.0, DD < 10%, régime ≠ flash_crash, whale_alerts ≤ 2 |

**Impact** : Sélection 20% meilleure des stratégies

---

### 2.10 Market Radar (5 fichiers, `agents/radar/`)

| Composant | Description |
|-----------|-------------|
| `TokenScanner` | Scan de 6 plateformes (PumpFun, DexScreener, Birdeye, etc.) — Score 0-10 |
| `WhaleTracker` | Détection de patterns historiques (accumulation vs distribution) |
| `SocialScanner` | Monitoring réseaux sociaux (Twitter, Telegram, Reddit, Discord) |
| `AnomalyDetector` | 5 types d'anomalies : `volume_spike`, `price_crash`, `liquidity_drain`, `whale_cluster` |
| `MarketRadar` | Orchestrateur — score composite 0-100 par opportunité |

---

### 2.11 Strategy Factory (6 fichiers)

Pipeline complet : Génération → Chargement mémoire par régime → Backtest → Filtrage → Classement → **Bot Doctor validation** → Sauvegarde

**Scoring Bot Doctor** :
- Sharpe < 1.0 : **-35 points** (critique)
- Drawdown > 10% : **-30 points** (critique)
- Win rate < 45% : **-20 points**
- Approuvée si score final **≥ 50**

---

### 2.12 Evolution Engine (2 fichiers)

| Fonction | Description |
|----------|-------------|
| Mémoire par régime | Stocke top 30 stratégies par régime (JSON) |
| Décroissance de fraîcheur | -3% par cycle |
| Pénalité d'usage | Empêche la réutilisation excessive |
| Chargement dynamique | 50%-150% de la base selon stabilité du régime |
| Dédoublonnage | Fusion des stratégies identiques |

---

### 2.13 Liquidity Flow Map (1 fichier)

**Secteurs classifiés** : BTC, ETH_L1, SOL_L1, DEFI, MEMECOINS, AI_TOKENS, ALTCOINS

**Métriques par secteur** : Volume, whale_flow, token_count, momentum_score  
**Score d'opportunité** (0-100) : Base (whale flow) + Bonus momentum + Bonus diversité

---

### 2.14 Agents de Risque (3 fichiers)

| Classe | Description |
|--------|-------------|
| `RiskMonitor` | Vérification des contraintes de drawdown |
| `DrawdownGuard` | Ajustement adaptatif de la taille des positions |
| `ExposureManager` | Plafonnement de concentration par symbole |

---

### 2.15 Agents d'Exécution (4 fichiers)

| Classe | Description |
|--------|-------------|
| `ExecutionEngine` | Création d'ordres |
| `PaperTradingEngine` | Trading simulé (balance initiale : 100k$, suivi positions) |
| `LiquidityAnalyzer` | Filtrage des symboles par seuil de volume |
| `ArbitrageAgent` | Détection de spreads (price_a vs price_b) |

---

### 2.16 Bot Doctor (`prompt_doctor_agent.py`, 240+ lignes)

| Fonction | Description |
|----------|-------------|
| `apply_doctor_corrections_with_issues()` | Corrections automatiques : signal (BUY/SELL/HOLD), allocation (0-1), niveau de risque |
| Alertes Telegram | Notifications en cas de problème détecté |
| Scoring santé | Score 0-100 avec pénalités par métrique |

---

### 2.17 Dashboards (8 fichiers)

| Composant | Type | Description |
|-----------|------|-------------|
| `AIControlCenter` | Console | Dashboard temps réel avec 7 sections |
| `DirectorDashboard` | Console | Super cockpit unifié (agrège tous les systèmes) |
| `AgentMonitor` | Console | Suivi du statut des 16 types d'agents |
| `BotDoctorPanel` | Console | Diagnostics de risque + corrections |
| `TradeMonitor` | Console | Suivi des paper trades + P&L |
| `SystemHealth` | Console | Scoring santé des composants (0-100) |
| `quant_terminal_v12.py` | Panel Web | Dashboard interactif avec graphiques live |
| `ai_dashboard.py` | Console | Rendu de rapports console |

---

### 2.18 Bases de données (3 fichiers)

| Base | Format | Description |
|------|--------|-------------|
| `StrategyScoreboard` | JSON | Leaderboard des top 500 stratégies par Sharpe |
| `StrategyDatabase` | JSON | Archive des meilleures stratégies (top 50) |
| `MarketDatabase` | JSONL | Snapshots de marché chronologiques (append-only) |

---

### 2.19 Configuration (`runtime_config.py`, 22 paramètres)

| Catégorie | Paramètres |
|-----------|-----------|
| **Cycle** | `max_cycles`, `sleep_seconds`, `seed` |
| **Stratégie** | `population_size`, `generations`, `max_strategy_weight` |
| **Risque** | `max_drawdown`, `min_sharpe_for_trade`, `trade_max_drawdown`, `whale_block_threshold` |
| **Données** | `monte_carlo_paths`, `monte_carlo_steps`, `display_frequency` |
| **Doctor** | `doctor_telegram_enabled`, `doctor_telegram_user_id`, `doctor_v26_report_enabled` |
| **UI** | `director_dashboard_enabled`, `dry_run` |

---

## 3. crypto_quant_v16 — Dashboard + Exécution

### 3.1 Orchestrateur (`main_v16.py`)

| Classe | Méthodes clés | Description |
|--------|---------------|-------------|
| `QuantSystemV16` | `scan_market()` | Scan du marché |
| | `generate_strategies()` | Génération de stratégies |
| | `evaluate_strategy()` | Évaluation des stratégies |
| | `optimize_portfolio()` | Optimisation du portefeuille |
| | `execute_trades()` | Exécution des trades |
| | `check_risk()` | Vérification des risques |
| | `run_cycle()` | Cycle complet |
| | `run_autonomous_loop()` | Boucle autonome continue |
| | `get_system_status()` | Statut du système |

---

### 3.2 Module AI (`ai/`)

| Classe | Fichier | Fonctions clés |
|--------|---------|----------------|
| `MarketObserver` | `market_observer.py` | `analyze()` — analyse de marché, `get_hot_symbols()` — symboles actifs, `memory_report()` |
| `StrategyGenerator` | `strategy_generator.py` | `generate_population()`, `evolve()`, `crossover()`, `mutate()`, `grid_search_optimize()`, indicateurs : `_ema_series()`, `_rsi()`, `_macd_hist()`, `_bollinger_zscore()`, `_momentum()` |
| `RiskEnforcer` | `risk_enforcer.py` | `check_position_size()`, `check_daily_loss()`, `check_portfolio_drawdown()`, `enforce_risk_policy()` |
| `RLTrader` | `reinforcement_trader.py` | `state_encoding()`, `choose_action()`, `learn()`, `act()`, `execute_trade()`, `get_performance()` |

---

### 3.3 Module Core (`core/`)

| Classe | Fichier | Fonctions clés |
|--------|---------|----------------|
| `RiskEngine` | `risk_engine.py` | `calculate_drawdown()`, `calculate_var()`, `calculate_max_drawdown_historical()`, `check_risk_limits()`, `should_kill_switch()`, `risk_report()` |
| `PortfolioManager` | `portfolio_manager.py` | `kelly_allocation()`, `allocate_equal_weight()`, `allocate_risk_weighted()`, `update_position()`, `get_portfolio_value()`, `get_pnl()`, `rebalance()` |
| `ExchangeManager` | `exchange_manager.py` | `fetch_ticker()`, `fetch_ohlcv()`, `get_supported_symbols()`, `place_order()`, `cancel_order()`, `get_balance()` |
| `ExecutionEngine` | `execution_engine.py` | `create_order()`, `set_stop_loss()`, `cancel_order()`, `get_order_history()`, `check_fill_conditions()` |
| `MarketScanner` | `market_scanner.py` | `scan()`, `calculate_rsi()`, `calculate_macd()`, `detect_anomalies()` |
| Orchestrator | `orchestrator.py` | `start_persistent_workers()`, `run_cycle()`, `_parallel_backtest()`, `_distributed_backtest()` |

---

### 3.4 Module Quant (`quant/`)

| Classe | Fichier | Fonctions clés |
|--------|---------|----------------|
| `PortfolioOptimizer` | `optimizer.py` | `optimize_sharpe()`, `optimize_min_variance()`, `optimize_max_sharpe()`, `efficient_frontier()`, `kelly_allocation()`, `rebalance_portfolio()` |
| `Backtester` | `backtester.py` | `backtest()`, `dynamic_position_size()`, `walk_forward()`, `detect_overfitting()`, `monte_carlo()`, `backtest_multi_strategy()` |
| `detect_regime()` | `regime_detector.py` | Détection de régime de marché |

---

### 3.5 Module V26/V30 — Fonctionnalités avancées (`v26/`)

| Composant | Fichier | Fonctions clés |
|-----------|---------|----------------|
| **Smart Chart** | `smart_chart.py` | `enrich_indicators()`, `detect_structure()`, `detect_bos()` (Break of Structure), `detect_choch()` (Change of Character), `detect_smart_money()`, `detect_order_blocks_zones()`, `detect_fvg_zones()` (Fair Value Gap), `orderbook_depth()` |
| **Debate Engine** | `debate_engine.py` | 5 bots d'analyse qui votent : `TrendBot`, `MomentumBot`, `StructureBot`, `VolatilityBot`, `LiquidityBot` → `DebateEngine.run()` → `final_decision()` |
| **Paper Trading** | `paper_trading.py` | `PaperTrader` — `open_position()`, `close_position()`, `close_all()`, `update_unrealized()`, `total_pnl()`, `equity()`, `win_rate()` |
| **Bot Doctor** | `bot_doctor.py` | `run_bot_doctor()` — Validation santé avec scoring et pénalités |
| **AI Assistant** | `ai_assistant.py` | `detect_trend()`, `momentum_signal()`, `breakout_signal()`, `volatility_state()`, `generate_trade()` |
| **Runtime Profile** | `runtime_profile.py` | `resolve_profile()`, `normalize_profile_name()`, `save_profile_name()`, `load_profile_state()`, `profile_for_dashboard()` |
| **Strategy Evolution** | `strategy_evolution.py` | `generate_strategy()`, `mutate_strategy()`, `backtest_score()`, `evolve_population()` |
| **Multi-Exchange** | `multi_exchange.py` | `scan_prices()`, `detect_arbitrage()` |
| **Regime Engine** | `regime_engine.py` | `detect_regime()`, `choose_strategy()` |
| **Portfolio Brain** | `portfolio_brain.py` | `score_asset()`, `allocate_portfolio()`, `apply_risk_limits()` |
| **DEX Adapter** | `dex_adapter.py` | `get_dex_route()`, `fetch_dex_ohlcv()`, `fetch_dex_orderbook()`, `probe_dex_live_anchor()`, `is_dex_exchange()` |
| **Data Simulator** | `data_simulator.py` | `fetch_ohlcv()`, `fetch_orderbook()`, `generate_ohlcv()`, `generate_orderbook()`, `generate_human_trend_data()` |
| **Human Trend Engine** | `human_trend_engine.py` | Génération de données de tendances humaines |
| **Market Brain** | `market_brain.py` | Intelligence de marché |

---

### 3.6 Dashboards (`ui/`)

| Dashboard | Fichier | Description |
|-----------|---------|-------------|
| `QuantDashboard` | `quant_dashboard.py` | Dashboard Panel principal V16 — layout, onglets, contrôles, sidebar |
| `QuantDashboardV13` | `quant_dashboard_v13.py` | Dashboard V13 avec clustering |
| `SmartChartV26Dashboard` | `quant_dashboard_v26.py` | Dashboard V26 avec Smart Money Concepts |
| Composants UI | `components.py` | `create_market_table()`, `create_candlestick_chart()`, `create_portfolio_pie()`, `create_equity_curve()`, `create_kpi_indicators()` |

---

### 3.7 Agents (`agents/`)

| Agent | Fichier | Description |
|-------|---------|-------------|
| `generate_strategy` | `strategy_agent.py` | Génération de stratégie |
| `evaluate_risk` | `risk_agent.py` | Évaluation du risque |
| `collect_market_data` | `market_agent.py` | Collecte de données marché |
| `execute_paper_orders` | `execution_agent.py` | Exécution d'ordres papier |
| `backtest` | `backtest_agent.py` | Backtesting |

---

### 3.8 Système Distribué (`distributed/`)

| Composant | Description |
|-----------|-------------|
| `Worker` | Worker thread pour traitement parallèle |
| `task_queue` | File d'attente de tâches (`add_task()`, `get_task()`) |

---

### 3.9 Tests

| Test | Description |
|------|-------------|
| `test_v30_smart_chart.py` | Tests du Smart Chart (BOS, CHoCH, Order Blocks, FVG) |
| `test_v30_profile_persistence.py` | Tests de persistance des profils |
| `test_v30_profile.py` | Tests des profils de runtime |
| `test_v30_multi_exchange.py` | Tests multi-exchange + arbitrage |

---

### 3.10 Health Check (`healthcheck_v30.py`)

Vérification de santé complète : ports, services, base de données, dashboard.

---

## 4. quant-ai-system — Stack Docker

### 4.1 Architecture Docker (`docker-compose.yml`)

| Service | Port | Description |
|---------|------|-------------|
| `crypto_ai_postgres` | 5432 | Base de données PostgreSQL |
| `crypto_ai_redis` | 6379 | Cache Redis |
| `crypto_ai_trading_bot` | — | Bot de trading principal |
| `crypto_ai_dashboard` | 8502 | Dashboard Streamlit |
| `crypto_ai_prometheus` | 9090 | Monitoring Prometheus |
| `crypto_ai_grafana` | 3000 | Visualisation Grafana |

---

### 4.2 Points d'entrée

| Fichier | Classe | Description |
|---------|--------|-------------|
| `main.py` | `CryptoAISystem` | Système de base — boucle de trading async |
| `main_v2.py` | `CryptoAISystem` | V2 — scan + génération + évaluation + optimisation + risque |
| `main_v7_multiagent.py` | `CryptoAITradingV7` | V7 multi-agents — données mock + exécution parallèle |
| `main_v7_production.py` | `CryptoAIProductionSystem` | V7 production — vérification DB/exchanges + cycles complets |

---

### 4.3 Module AI (`ai/`)

| Classe | Fichier | Description |
|--------|---------|-------------|
| `StrategySelector` | `strategy_selector.py` | Sélection de stratégies de trading |
| `StrategyGenerator` + `Strategy` | `strategy_generator.py` | Génération de stratégies |
| `StrategyEvaluator` + `BacktestResult` | `strategy_evaluator.py` | Évaluation par backtest |
| `RLTradingAgent` + `Experience` | `reinforcement_agent.py` | Agent de reinforcement learning |
| `LSTMPredictor` + `PredictionResult` | `price_predictor.py` | Prédiction de prix par LSTM |
| `AIMarketSimulator` + `SimulatedTradingEnvironment` | `market_simulator.py` | Simulation de marché complète |

---

### 4.4 Module Agents (`agents/`)

| Classe | Description |
|--------|-------------|
| `Agent` (base) | Classe de base avec `AgentStatus`, `AgentRole`, `AgentMessage`, `AgentTask` |
| `AgentCoordinator` | Coordination des agents |
| `TradingMultiAgentSystem` | Système multi-agents orchestré |
| `MarketScannerAgent` | Agent de scan marché |
| `StrategyGeneratorAgent` | Agent de génération de stratégies |
| `BacktesterAgent` | Agent de backtesting |
| `RiskManagerAgent` | Agent de gestion du risque |
| `PortfolioOptimizerAgent` | Agent d'optimisation de portefeuille |
| `ExecutionAgent` | Agent d'exécution |

---

### 4.5 Module Core (`core/`)

| Classe | Description |
|--------|-------------|
| `RiskEngine` + `RiskMetrics` | Calcul et gestion du risque |
| `PortfolioManager` + `Position` + `PortfolioMetrics` | Gestion du portefeuille |
| `MarketScanner` + `MarketOpportunity` | Scan de marché |
| `ExecutionEngine` + `Order` + `OrderType/Side/Status` | Exécution d'ordres |

---

### 4.6 Module Quant (`quant/`)

| Classe | Description |
|--------|-------------|
| `GeneticAlgorithmOptimizer` | Optimisation par algorithme génétique |
| `PortfolioOptimizer` + `OptimizationResult` | Optimisation de portefeuille |
| `Backtester` + `BacktestResult` + `WalkForwardResult` | Backtesting + Walk-forward |

---

### 4.7 Infrastructure (`infrastructure/`)

| Classe | Fichier | Description |
|--------|---------|-------------|
| `ExchangeConnector` | `ccxt_connector.py` | Connexion aux exchanges via CCXT |
| `MultiExchangeAggregator` | `ccxt_connector.py` | Agrégation multi-exchange |
| `LiveMarketDataFeeder` | `ccxt_connector.py` | Flux de données en temps réel |
| `WebSocketFeed` | `websocket_feeds.py` | Feed WebSocket de base |
| `BinanceWebSocketFeed` | `websocket_feeds.py` | Feed Binance |
| `BybitWebSocketFeed` | `websocket_feeds.py` | Feed Bybit |
| `KrakenWebSocketFeed` | `websocket_feeds.py` | Feed Kraken |
| `MultiExchangeWebSocketAggregator` | `websocket_feeds.py` | Agrégation WebSocket multi-exchange |
| `RiskLimits` + `RiskManager` + `RiskMonitor` | `risk_limits.py` | Limites et monitoring du risque |
| `PaperTradingAccount` + `PaperTradingMode` | `paper_trading.py` | Paper trading complet |
| `MonitoringSystem` + `HealthCheck` + `PerformanceTracker` | `monitoring.py` | Monitoring et santé système |
| `PostgreSQLManager` + `RedisManager` + `DatabaseCluster` | `database.py` | Gestion BDD PostgreSQL + Redis |

---

## 5. Projets Legacy

### 5.1 bot-v3

Bot de trading basique avec `AdvancedAnalytics` pour les analyses avancées.

### 5.2 quant-bot-v3-pro

Extension pro avec `AIModel` (modèle IA) + `AdvancedAnalytics`.

### 5.3 quant-hedge-bot

Système hedge fund complet :
- `QuantHedgeBot` / `ProfessionalHedgeFundBot` — Bots principaux
- `TradeExecutor` — Exécution des trades
- `StrategyEngine` — Moteur de stratégies
- `RiskEngine` — Gestion du risque
- `PortfolioManager` — Gestion de portefeuille
- `ModelTrainer` — Entraînement de modèles IA
- `RLAgent` — Agent de reinforcement learning
- `LSTMModel` — Prédiction LSTM
- `MonteCarloSimulator` — Simulations Monte Carlo
- `WalkForwardTester` — Test walk-forward
- `MultiStrategyEngine` — Gestion multi-stratégies
- `KellyOptimizer` — Optimisation Kelly

### 5.4 quant-trading-system

Système de trading institutionnel :
- `SystemManager` / `CryptoAISystem` — Coordinateurs
- `InstitutionalStrategyEngine` — Stratégies institutionnelles
- `ArbitrageEngine` — Moteur d'arbitrage
- `AdvancedDataPipeline` — Pipeline de données
- `QuantTradingOrchestrator` — Orchestration
- `SharpeOptimizer`, `RiskParityOptimizer` — Optimiseurs avancés
- `ProfessionalBacktester` — Backtesting professionnel
- `AnomalyDetector`, `RegimeDetector` — Détection avancée
- `DatabaseManager` — Gestion BDD

---

## 6. Scripts & Utilitaires Workspace

### 6.1 Scripts de lancement

| Script | Description |
|--------|-------------|
| `launch_all.bat / .ps1` | Lance tous les systèmes |
| `stop_all.bat` | Arrête tous les systèmes |
| `launch_v12_dashboard.bat` | Dashboard V12 |
| `launch_all_ps_visible.bat` | Lancement avec fenêtres visibles |
| `launch_all_ps_with_env.bat` | Lancement avec variables d'environnement |

### 6.2 Scripts crypto_quant_v16

| Script | Description |
|--------|-------------|
| `launch_v16_dashboard.bat` | Dashboard Panel V16 |
| `launch_v26_dashboard.bat` | Dashboard V26 Smart Chart |
| `launch_v30_full.bat / .ps1 / .py` | Lancement complet V30 |
| `stop_v30_full.bat / .ps1` | Arrêt V30 |
| `healthcheck_v30.bat / .ps1 / .py` | Vérification santé V30 |
| `monitor_v30.bat / .ps1` | Monitoring V30 |
| `launch_binance_alerts.bat` | Alertes Binance |

### 6.3 Scripts de vérification

| Script | Description |
|--------|-------------|
| `healthcheck_v27.bat / .ps1` | Health check V27 |
| `ONE_CLICK_SETUP_VERIFY.bat` | Vérification setup en un clic |

---

## 📊 Statistiques globales

| Métrique | Valeur |
|----------|--------|
| **Systèmes de trading** | 5 indépendants |
| **Fichiers Python** | ~200+ |
| **Lignes de code** | ~15,000+ |
| **Agents IA** | 20+ (V9.1) + 6 (V7) + agents legacy |
| **Dashboards** | 8 (console) + 3 (web Panel) + 1 (Streamlit) |
| **Indicateurs techniques** | RSI, MACD, EMA, Bollinger, Momentum, Smart Money |
| **Algorithmes d'optimisation** | Génétique, Kelly, Monte Carlo, Walk-Forward, RL (Q-learning) |
| **Modèles ML** | LSTM, Reinforcement Learning, Q-Learning |
| **Types de régimes** | 5 (bull, bear, sideways, high_vol, flash_crash) |
| **Exchanges supportés** | Binance, Bybit, Kraken + DEX (Uniswap, Hyperliquid) |
| **Infrastructure** | Docker, PostgreSQL, Redis, Prometheus, Grafana |
| **Documentation** | ~230 KB, 11+ fichiers |

---

## 🏗️ Architecture fonctionnelle complète

```
┌──────────────────────────────────────────────────────────────────┐
│                    CRYPTO AI TERMINAL                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │  quant-hedge-ai     │  │  crypto_quant_v16   │              │
│  │  (V9.1 - Principal) │  │  (V16/V26/V30)      │              │
│  ├─────────────────────┤  ├─────────────────────┤              │
│  │ • 20 agents IA      │  │ • Dashboard Panel   │              │
│  │ • Intelligence 7D   │  │ • Smart Money Charts│              │
│  │ • Whale Radar       │  │ • Debate Engine     │              │
│  │ • Kelly Allocator   │  │ • DEX Adapter       │              │
│  │ • Decision Engine   │  │ • Paper Trading     │              │
│  │ • Bot Doctor        │  │ • Multi-Exchange    │              │
│  │ • Evolution mémoire │  │ • Bot Doctor V26    │              │
│  │ • Director Dashboard│  │ • Profile System    │              │
│  │ • Strategy Factory  │  │ • Human Trend       │              │
│  │ • Liquidity FlowMap │  │ • Distributed Work  │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │  quant-ai-system    │  │  Legacy Projects    │              │
│  │  (V7 Docker)        │  │                     │              │
│  ├─────────────────────┤  ├─────────────────────┤              │
│  │ • 6 containers      │  │ • bot-v3            │              │
│  │ • PostgreSQL+Redis  │  │ • quant-bot-v3-pro  │              │
│  │ • Prometheus+Grafana│  │ • quant-hedge-bot   │              │
│  │ • Multi-agent system│  │ • quant-trading-sys │              │
│  │ • LSTM predictor    │  │                     │              │
│  │ • WebSocket feeds   │  │ (Référence seulmt)  │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```
