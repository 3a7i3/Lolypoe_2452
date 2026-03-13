"""
Configuration Centrale - Quant Hedge Bot
==========================================
Parametres de trading, AI, et risque pour le hedge fund bot
"""

# ===== MARCHE & DONNEES =====
SYMBOLS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD', 'XRP-USD']
INTERVALS = {'1h': '1h', '4h': '4h', '1d': '1d'}  # pour multi-timeframe
PRIMARY_INTERVAL = '1h'
LOOKBACK_PERIOD = 200  # Donnees historiques a garder

# ===== PORTFOLIO MANAGEMENT =====
INITIAL_CAPITAL = 100000
ALLOCATION_STRATEGY = 'equal'  # equal, risk-parity, momentum
MAX_POSITION_SIZE = 0.25  # Max 25% du capital par position
MIN_POSITION_SIZE = 0.05  # Min 5% du capital
REBALANCE_FREQUENCY = 'daily'  # ou 'weekly', 'monthly'

# ===== RISK MANAGEMENT =====
MAX_DRAWDOWN_PERCENT = 0.15  # 15% max drawdown
DAILY_LOSS_LIMIT = 0.03  # 3% max perte journaliere
STOP_LOSS_PERCENT = 0.08  # 8% stop loss
TAKE_PROFIT_PERCENT = 0.15  # 15% take profit
TRAILING_STOP_PERCENT = 0.05  # 5% trailing stop

# ===== INDICATEURS TECHNIQUES =====
SMA_SHORT = 20
SMA_LONG = 50
SMA_LONG_TERM = 200
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# ===== CONDITIONS DE TRADING =====
MIN_VOLUME = 1000000  # Volume min pour trader
MAX_SLIPPAGE = 0.001  # Max 0.1% slippage
MIN_VOLATILITY = 0.005  # Min volatilite acceptable
MAX_TRADES_PER_DAY = 10
MIN_TRADE_INTERVAL = 300  # 5 minutes entre trades
TRADE_ONLY_DURING_MARKET_HOURS = False

# ===== MACHINE LEARNING =====
MODEL_TYPE = 'lstm'  # ou 'random_forest', 'gradient_boosting'
SEQUENCE_LENGTH = 60  # Nombre de jours precedents pour LSTM
PREDICTION_HORIZON = 5  # Prediction 5 jours en avant
TEST_SIZE = 0.2
VALIDATION_SIZE = 0.1
EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.001

# ===== REINFORCEMENT LEARNING =====
RL_ENABLED = True
RL_EPSILON = 0.1  # Probabilite d'exploration
RL_GAMMA = 0.95  # Discount factor
RL_LR = 0.001

# ===== BACKTESTING =====
BACKTEST_START_DATE = '2023-01-01'
BACKTEST_END_DATE = '2025-12-31'
BACKTEST_CAPITAL = 10000
BACKTEST_COMMISSION = 0.001  # 0.1% commission
BACKTEST_SLIPPAGE = 0.0005

# ===== REGIME DETECTION =====
REGIME_WINDOW = 60  # Detect regime sur 60 jours
REGIMES = ['BULL', 'BEAR', 'SIDEWAYS']
REGIME_THRESHOLD = 0.6

# ===== ANOMALITY DETECTION =====
ANOMALY_THRESHOLD = 2.5  # Standard deviations
ANOMALY_WINDOW = 30

# ===== NOTIFICATIONS =====
TELEGRAM_ENABLED = False
TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""
EMAIL_ENABLED = False
EMAIL_ADDRESS = ""
SLACK_ENABLED = False
SLACK_WEBHOOK = ""

# ===== LOGGING =====
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_DIR = 'logs'
LOG_FILE = 'quant_hedge_bot.log'

# ===== DATABASE =====
DATABASE_TYPE = 'sqlite'  # ou 'postgresql'
DATABASE_PATH = 'data/trades/quant_hedge.db'

# ===== SCHEDULER =====
SCHEDULE_ENABLED = True
RUN_INTERVAL_MINUTES = 60  # Executer le bot toutes les heures
MARKET_OPEN_TIME = '09:30'  # heure ouverture marche
MARKET_CLOSE_TIME = '16:00'  # heure fermeture marche
TIMEZONE = 'UTC'

# ===== DEBUG =====
DEBUG_MODE = False
VERBOSE = True
SAVE_INTERMEDIATE_DATA = True

# ===== PROFESSIONAL HEDGE FUND MODE =====
PROFESSIONAL_MODE = True
PROFESSIONAL_24_7_MODE = True
PROFESSIONAL_RUN_INTERVAL_MINUTES = 5

# ===== CRYPTOCURRENCY UNIVERSE =====
# Monitor 500+ cryptocurrencies across multiple exchanges
MONITOR_CRYPTO_UNIVERSE = True
NUM_CRYPTO_TO_MONITOR = 500
EXCHANGES_TO_MONITOR = ['binance', 'kraken', 'coinbase', 'kucoin', 'huobi']

# ===== MULTIPLE STRATEGIES =====
ENABLED_STRATEGIES = [
    'trend_following',
    'mean_reversion',
    'breakout',
    'volatility_trading',
    'market_making'
]
STRATEGY_ENSEMBLE_METHOD = 'voting'  # voting, weighted, consensus
STRATEGY_CONFIDENCE_THRESHOLD = 0.65

# ===== ADVANCED QUANTITATIVE TOOLS =====
# Regime Detection
REGIME_DETECTION_ENABLED = True
REGIME_DETECTION_METHOD = 'sma'  # sma, returns, adx

# Anomaly Detection
ANOMALY_DETECTION_ENABLED = True
ANOMALY_DETECTION_METHOD = 'zscore'  # zscore, isolation_forest, mahalanobis

# Feature Engineering
FEATURE_ENGINEERING_ENABLED = True
NUM_ENGINEERED_FEATURES = 10

# Monte Carlo Simulation
MONTE_CARLO_ENABLED = True
MONTE_CARLO_SIMULATIONS = 10000
MONTE_CARLO_FORECAST_DAYS = 252

# Walk-Forward Backtesting
WALK_FORWARD_ENABLED = True
WALK_FORWARD_OPT_PERIOD = 252  # 1 year
WALK_FORWARD_TEST_PERIOD = 63  # 3 months

# ===== PORTFOLIO OPTIMIZATION =====
# Kelly Criterion
KELLY_CRITERION_ENABLED = True
KELLY_FRACTION = 0.5  # Half Kelly for risk management
KELLY_MAX_ALLOCATION = 0.25  # Max 25% per position with Kelly

# Risk Parity
RISK_PARITY_ENABLED = True
RISK_PARITY_TARGET_VOL = 0.12  # 12% target volatility

# Volatility Targeting
VOLATILITY_TARGET_ENABLED = True
TARGET_VOLATILITY = 0.15  # 15% annualized volatility

# ===== DATA PIPELINE =====
# High-performance async processing
ASYNC_DATA_PROCESSING = True
USE_DATA_CACHING = True
CACHE_EXPIRY_MINUTES = 5
DATA_NORMALIZATION_METHOD = 'zscore'  # zscore, minmax, robust

# Batch processing for performance
BATCH_PROCESS_SIZE = 100
USE_PARALLEL_PROCESSING = True
NUM_WORKERS = 4

# ===== DASHBOARD & MONITORING =====
DASHBOARD_ENABLED = True
DASHBOARD_REFRESH_INTERVAL = 5  # seconds
LIVE_MONITORING_ENABLED = True

# Real-time metrics to track
TRACKED_METRICS = [
    'pnl',
    'pnl_percent',
    'sharpe_ratio',
    'sortino_ratio',
    'max_drawdown',
    'win_rate',
    'trade_count',
    'exposure',
    'leverage'
]

# ===== PRODUCTION SETTINGS =====
PRODUCTION_MODE = True
PRODUCTION_CAPITAL = 100000  # Starting capital in production
PRODUCTION_LOG_LEVEL = 'INFO'
PRODUCTION_ERROR_EMAIL = ''
PRODUCTION_ALERT_TELEGRAM = False

# Hedging
USE_HEDGING = True
HEDGING_RATIO = 0.5  # Hedge 50% of long exposure

# Diversification limits
MIN_NUM_POSITIONS = 5
MAX_NUM_POSITIONS = 50
MIN_SECTOR_ALLOCATION = 0.05
MAX_SECTOR_ALLOCATION = 0.40

# Slippage and costs
SLIPPAGE_MODEL = 'linear'  # linear, square_root, fixed
SLIPPAGE_RATE = 0.0005  # 5 bps
COMMISSION_RATE = 0.001  # 10 bps
FINANCING_COST_PERCENT = 0.05  # Annual financing cost

# ===== PERFORMANCE BENCHMARKS =====
BENCHMARK_SYMBOLS = ['BTC-USD', 'ETH-USD']  # For comparison
TARGET_SHARPE_RATIO = 1.5
TARGET_ANNUAL_RETURN = 0.25  # 25% annually
TARGET_MAX_DRAWDOWN = 0.20  # 20% max

# ===== EXECUTION PARAMETERS =====
ORDER_TYPE = 'limit'  # limit, market, smart
LIMIT_ORDER_OFFSET_PERCENT = 0.002  # 0.2% above/below market
TIME_IN_FORCE = 'GTC'  # GTC, IOC, FOK
SMART_ORDER_ROUTING = True

# ===== STRESS TESTING =====
STRESS_TEST_ENABLED = True
STRESS_TEST_SCENARIOS = ['crisis', 'flash_crash', 'liquidity_crunch']
MAX_ACCEPTABLE_VAR_95 = -0.25  # Don't accept positions with >25% VaR 95%
