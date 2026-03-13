"""
Professional Quant Trading System V5 - Configuration
1000+ crypto monitoring, multi-strategies, AI prediction, arbitrage
"""

# System Configuration
SYSTEM_NAME = "Quant Trading System V5"
VERSION = "5.0.0"
PRODUCTION_MODE = True
DEBUG_MODE = False

# ============ MARKET SCANNER ============
CRYPTO_UNIVERSE_SIZE = 1500  # Monitor 1500+ cryptos (institutional-grade)
TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']
PRIMARY_TIMEFRAME = '1h'
LOOKBACK_PERIODS = {
    '1m': 1440,    # 24 hours
    '5m': 288,     # 24 hours
    '15m': 96,     # 24 hours
    '1h': 24,      # 24 hours
    '4h': 6,       # 24 hours
    '1d': 365      # 1 year
}

# ============ EXCHANGES (Institutional-Grade) ============
EXCHANGES = {
    'binance': {
        'name': 'Binance',
        'enabled': True,
        'weight': 0.45,
        'fetch_limit': 500,
        'rate_limit': 1200,
        'taker_fee': 0.001,
        'maker_fee': 0.001
    },
    'bybit': {
        'name': 'Bybit',
        'enabled': True,
        'weight': 0.30,
        'fetch_limit': 350,
        'rate_limit': 600,
        'taker_fee': 0.001,
        'maker_fee': 0.0001
    },
    'coinbase': {
        'name': 'Coinbase Pro',
        'enabled': True,
        'weight': 0.15,
        'fetch_limit': 200,
        'rate_limit': 500,
        'taker_fee': 0.006,
        'maker_fee': 0.004
    },
    'kraken': {
        'name': 'Kraken',
        'enabled': True,
        'weight': 0.10,
        'fetch_limit': 150,
        'rate_limit': 300,
        'taker_fee': 0.0026,
        'maker_fee': 0.0016
    }
}

# ============ TRADING STRATEGIES (Institutional-Grade) ============
ENABLED_STRATEGIES = [
    'trend_following',
    'mean_reversion',
    'volatility_breakout',
    'statistical_arbitrage',
    'market_making'
]

STRATEGY_WEIGHTS = {
    'trend_following': 0.30,
    'mean_reversion': 0.25,
    'volatility_breakout': 0.25,
    'statistical_arbitrage': 0.15,
    'market_making': 0.05
}

# Strategy hyperparameters
STRATEGY_PARAMS = {
    'trend_following': {
        'sma_short': 20,
        'sma_long': 50,
        'rsi_threshold': 30,
        'stop_loss': 0.03,
        'take_profit': 0.08,
        'min_volume': 100000
    },
    'mean_reversion': {
        'lookback': 20,
        'upper_bb': 2.0,
        'lower_bb': 2.0,
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        'mean_reversion_period': 5
    },
    'volatility_breakout': {
        'atr_period': 14,
        'atr_threshold': 2.5,
        'breakout_lookback': 20,
        'volume_threshold': 1.5
    },
    'statistical_arbitrage': {
        'correlation_threshold': 0.85,
        'zscore_threshold': 2.0,
        'hedge_ratio_lookback': 60,
        'pair_selection_limit': 50
    },
    'market_making': {
        'bid_ask_spread_target': 0.002,
        'inventory_limit': 0.05,
        'order_refresh_time': 60,
        'position_limit': 0.02
    }
}

# ============ POSITION MANAGEMENT ============
MAX_POSITIONS = 50
MIN_POSITION_SIZE = 0.01  # 1% of capital
MAX_POSITION_SIZE = 0.05  # 5% of capital
TRAILING_STOP_PERCENT = 2.0
TAKE_PROFIT_PERCENT = 8.0
STOP_LOSS_PERCENT = 3.0

# ============ RISK MANAGEMENT ============
MAX_DAILY_LOSS = 0.02  # 2% max daily loss
MAX_DRAWDOWN = 0.15  # 15% max drawdown
PORTFOLIO_VOLATILITY_TARGET = 0.15  # 15% annual volatility
MAX_LEVERAGE = 2.0
MIN_SHARPE_RATIO = 1.0

# ============ ARBITRAGE ============
ARBITRAGE_ENABLED = True
ARBITRAGE_MIN_SPREAD = 0.005  # 0.5% minimum spread
ARBITRAGE_MAX_LATENCY = 100  # milliseconds
ARBITRAGE_CAPITAL_ALLOCATION = 0.10  # 10% of capital

# ============ LSTM MODEL (Deep Learning) ============
LSTM = {
    'enabled': True,
    'sequence_length': 120,  # Longer sequences for context
    'epochs': 100,
    'batch_size': 32,
    'dropout': 0.3,
    'recurrent_dropout': 0.2,
    'layers': 3,
    'units_per_layer': [128, 64, 32],
    'optimizer': 'adam',
    'learning_rate': 0.001,
    'loss_function': 'mse',
    'early_stopping': True,
    'patience': 10,
    'activation': 'relu',
    'output_activation': 'linear',
    'validation_split': 0.2,
    'use_bidirectional': True,
    'return_sequences': [True, True, False],  # Last layer returns single value
}

# ============ RANDOM FOREST MODEL ============
RANDOM_FOREST = {
    'enabled': True,
    'n_estimators': 200,
    'max_depth': 20,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'max_features': 'sqrt',
    'criterion': 'gini',  # gini or entropy
    'random_state': 42,
    'n_jobs': -1,  # Use all cores
    'oob_score': True,  # Out-of-bag evaluation
    'verbose': 0,
}

# ============ REINFORCEMENT LEARNING AGENT ============
RL_AGENT = {
    'enabled': True,
    'algorithm': 'dqn',  # dqn, policy_gradient, a3c, ppo
    'gamma': 0.99,  # Discount factor
    'epsilon_start': 1.0,
    'epsilon_decay': 0.995,
    'epsilon_min': 0.01,
    'learning_rate': 0.001,
    'buffer_size': 10000,  # Replay buffer
    'update_frequency': 4,  # Updates per step
    'target_update_frequency': 1000,  # Hard update
    'reward_scaling': 1.0,
    'use_double_q': True,
    'use_dueling': True,
    'use_prioritized_replay': True,
    'network_layers': [128, 64, 32],
    'activation': 'relu',
    'batch_normalization': True,
    'max_steps_per_episode': 500,
    'episodes_for_training': 100,
}

# ============ XGBOOST (Gradient Boosting) ============
XGBOOST = {
    'enabled': True,
    'n_estimators': 200,
    'max_depth': 7,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'binary:logistic',  # For classification or binary:logistic
    'eval_metric': 'auc',
    'random_state': 42,
    'n_jobs': -1,
}

# ============ ENSEMBLE MODEL ============
ENSEMBLE_MODEL = {
    'enabled': True,
    'methods': ['lstm', 'random_forest', 'xgboost', 'rl_agent'],
    'weights': {
        'lstm': 0.4,
        'random_forest': 0.3,
        'xgboost': 0.2,
        'rl_agent': 0.1
    },
    'voting_type': 'weighted_average',  # weighted_average, majority, stacking
    'enable_stacking': True,
    'meta_learner': 'logistic_regression',  # Model to combine predictions
}

# ============ AI/ML MODELS (Consolidated) ============
AI_MODELS_ENABLED = True
PRICE_PREDICTION_ENABLED = True
MODEL_UPDATE_FREQUENCY = 12  # hours (more frequent for institutional)
PREDICTION_WINDOW = 5  # periods ahead
CONFIDENCE_THRESHOLD = 0.65
ENABLE_TRANSFER_LEARNING = True
ENABLE_ACTIVE_LEARNING = True
MODEL_RETRAINING_INTERVAL = 168  # hours (weekly) for major retraining

# ============ BACKTESTING ============
BACKTEST_ENABLED = True
BACKTEST_START_DATE = '2024-01-01'
BACKTEST_END_DATE = '2025-12-31'
BACKTEST_INITIAL_CAPITAL = 100000
BACKTEST_COMMISSION = 0.001  # 0.1% per trade
WALK_FORWARD_WINDOW = 63  # days

# ============ PORTFOLIO OPTIMIZATION (Institutional-Grade) ============
OPTIMIZATION_METHODS = ['kelly_criterion', 'risk_parity', 'sharpe_maximization']
PRIMARY_OPTIMIZATION = 'kelly_criterion'
KELLY_FRACTION = 0.5  # Half-Kelly for safety
REBALANCE_FREQUENCY = 1  # hours
CORRELATION_THRESHOLD = 0.7
MAX_SECTOR_ALLOCATION = 0.30
EXPECTED_ANNUAL_RETURN = 0.25  # 25% target
TARGET_VOLATILITY = 0.15  # 15% target

# ============ MONTE CARLO (Advanced) ============
MONTE_CARLO_SIMULATIONS = 50000  # Institutional-grade
MONTE_CARLO_DAYS = 252
MONTE_CARLO_CONFIDENCE_LEVELS = [0.90, 0.95, 0.99]
VAR_CONFIDENCE_LEVEL = 0.95
CVAR_CONFIDENCE_LEVEL = 0.99
STRESS_TEST_SCENARIOS = ['market_crash', 'flash_crash', 'liquidity_crisis', 'regulatory_shock']

# ============ BACKTESTING (Professional) ============
BACKTEST_MODE = 'walk_forward'  # walk_forward, rolling, anchored
BACKTEST_WINDOW = 252  # days
WALK_FORWARD_STEP = 63  # days
BACKTEST_INITIAL_CAPITAL = 1000000  # $1M
BACKTEST_COMMISSION_TYPE = 'percentage'  # percentage, fixed
BACKTEST_COMMISSION_VALUE = 0.001  # 0.1%
BACKTEST_SLIPPAGE = 0.0005  # 0.05%
INCLUDE_REALISTIC_CROSSING = True
REALISTIC_CROSSING_COST = 0.0002

# ============ DATABASE (Institutional) ============
DATABASE_TYPE = 'sqlite'  # Can be upgraded to PostgreSQL
DATABASE_PATH = 'data/institutional_trading.db'
CACHE_ENABLED = True
CACHE_EXPIRY = 60  # seconds (more aggressive)
MAX_CACHE_SIZE = 10000  # entries
CACHE_TYPE = 'redis'  # redis or memory
ENABLE_PERSISTENCE = True
PERSIST_INTERVAL = 300  # seconds

# ============ DATA PIPELINE (High-Performance) ============
ASYNC_ENABLED = True
ASYNC_BATCH_SIZE = 50  # Parallel requests
WORKER_THREADS = 16  # More workers for institutional scale
DATA_UPDATE_INTERVAL = 30  # seconds (more frequent)
HISTORICAL_DATA_DAYS = 1095  # 3 years
ENABLE_DATA_VALIDATION = True
ENABLE_DATA_DEDUPLICATION = True
MAX_DATA_RETRIES = 5
RETRY_BACKOFF_FACTOR = 2

# ============ FEATURE ENGINEERING (Advanced) ============
TECHNICAL_INDICATORS = [
    # Trend Indicators
    'sma_20', 'sma_50', 'sma_200',
    'ema_12', 'ema_26', 'ema_50', 'ema_200',
    # Volume & Momentum
    'rsi_14', 'rsi_21', 'rsi_28',
    'macd', 'macd_signal', 'macd_histogram',
    'stoch_k', 'stoch_d', 'williams_r',
    # Volatility
    'bb_20', 'bb_50', 'atr_14', 'atr_21',
    # Trend Strength
    'adx_14', 'adx_21', 'cci_20', 'cmf', 'mfi',
    # Price Action
    'obv', 'vwap', 'hma_50'
]

FEATURE_ENGINEERING = {
    'enabled': True,
    'lookback': 120,  # Extended for ML models
    'scaling_method': 'z_score',  # z_score, min_max, robust, standard
    'enable_cross_validation': True,
    'enable_feature_selection': True,
    'min_feature_importance': 0.02,
    'enable_pca': False,
    'pca_components': 20,
    'add_lagged_features': True,
    'lagged_periods': [1, 2, 3, 5, 10],  # Temporal dependencies
    'add_volume_features': True,
    'add_return_features': True
}

# ============ ANOMALY DETECTION (Advanced) ============
ANOMALY_DETECTION = {
    'enabled': True,
    'method': 'isolation_forest',  # zscore, isolation_forest, mahalanobis, local_outlier_factor
    'threshold': 3.0,  # standard deviations for zscore
    'contamination': 0.05,  # for isolation forest
    'min_volume': 10000,  # USDT
    'sensitivity': 0.95,  # 0.90-1.0
    'detection_interval': 300,  # seconds
    'alert_on_anomaly': True,
    'anomaly_cooldown': 3600,  # seconds before next alert
    # Specific anomalies to detect
    'detect_volume_spike': True,
    'volume_spike_threshold': 2.0,  # 2x normal volume
    'detect_price_gap': True,
    'price_gap_threshold': 0.05,  # 5% gap
    'detect_volatility_spike': True,
    'volatility_spike_threshold': 1.5,  # 1.5x normal volatility
    'detect_correlation_break': True,  # For pairs trading
    'correlation_break_threshold': 0.3,  # Sudden correlation drop
}

# ============ REGIME DETECTION (Advanced) ============
REGIME_DETECTION = {
    'enabled': True,
    'method': 'hmm',  # hmm, markov_chain, cluster, kalman_filter
    'window': 30,  # periods
    'num_regimes': 5,  # Number of market regimes
    'regimes': ['STRONG_BULL', 'BULL', 'NEUTRAL', 'BEAR', 'STRONG_BEAR'],
    'confidence_threshold': 0.70,  # Min confidence to switch regimes
    'transition_matrix_update_freq': 24,  # hours
    # Regime indicators
    'use_volatility': True,
    'use_momentum': True,
    'use_trend': True,
    'use_volume': True,
    # Regime-specific thresholds
    'bull_threshold': 0.6,
    'bear_threshold': -0.6,
    'neutral_range': (-0.3, 0.3),
    'volatility_percentiles': [25, 50, 75],  # For classification
}

# ============ ENHANCED ML MODEL PARAMETERS ============
ML_TRAINING = {
    'enabled': True,
    'update_frequency': 12,  # hours
    'prediction_window': 5,  # periods ahead
    'confidence_threshold': 0.65,
    'enable_ensemble': True,
    'enable_transfer_learning': True,
    'enable_active_learning': True,
    'train_test_split': 0.8,
    'validation_split': 0.1,
}

# ============ EXECUTION ============
ORDER_TYPE = 'limit'  # limit, market
EXECUTION_SLIPPAGE = 0.002  # 0.2%
EXECUTION_TIMEOUT = 60  # seconds
MIN_ORDER_NOTIONAL = 10  # USDT

# ============ NOTIFICATIONS ============
NOTIFICATIONS_ENABLED = True
TELEGRAM_ENABLED = False
EMAIL_ENABLED = False
SLACK_ENABLED = False

# ============ LOGGING ============
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = 'logs/quant_system.log'
LOG_MAX_SIZE = 10485760  # 10 MB
LOG_BACKUP_COUNT = 5

# ============ DASHBOARD ============
DASHBOARD_PORT = 8501
DASHBOARD_HOST = '0.0.0.0'
DASHBOARD_UPDATE_INTERVAL = 5  # seconds
DASHBOARD_REFRESH_RATE = 1  # Hz

# ============ SYSTEM MONITORING ============
MONITOR_CPU = True
MONITOR_MEMORY = True
MONITOR_DISK = True
HEALTH_CHECK_INTERVAL = 60  # seconds
RESTART_ON_CRASH = True

# ============ COMPLIANCE ============
AUDIT_LOGGING = True
TRADE_AUDIT_FILE = 'logs/trades_audit.log'
POSITION_AUDIT_FILE = 'logs/positions_audit.log'
DAILY_RECONCILIATION = True

print("[CONFIG] Quant Trading System V5 configuration loaded")
