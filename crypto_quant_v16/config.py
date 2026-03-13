"""
Configuration – V16 System Configuration
API keys, assets, parameters, and settings
"""

import os
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROJECT SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROJECT_NAME = "Crypto Quant V16"
VERSION = "1.0.0"
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXCHANGE SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXCHANGES = {
    'binance': {
        'apiKey': os.getenv('BINANCE_API_KEY', ''),
        'secret': os.getenv('BINANCE_SECRET', ''),
    },
    'bybit': {
        'apiKey': os.getenv('BYBIT_API_KEY', ''),
        'secret': os.getenv('BYBIT_SECRET', ''),
    },
    'kraken': {
        'apiKey': os.getenv('KRAKEN_API_KEY', ''),
        'secret': os.getenv('KRAKEN_SECRET', ''),
    }
}

PRIMARY_EXCHANGE = 'binance'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRADING ASSETS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOP_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
    "ADA/USDT", "AVAX/USDT", "DOGE/USDT", "DOT/USDT", "MATIC/USDT",
    "LINK/USDT", "UNI/USDT", "ATOM/USDT", "LTC/USDT", "ETC/USDT",
]

PORTFOLIO_ALLOCATION = {
    "BTC": 0.35,
    "ETH": 0.25,
    "SOL": 0.15,
    "AVAX": 0.15,
    "LINK": 0.10,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRADING PARAMETERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRADING_MODE = 'paper'  # 'paper' or 'live'
INITIAL_CAPITAL = 10000.0
TRADING_FEE = 0.001  # 0.1%
SLIPPAGE = 0.0005    # 0.05%
POSITION_SIZE_MAX = 0.10  # Max 10% per position
STOP_LOSS_PCT = 0.05  # 5% stop loss

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RISK MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAX_PORTFOLIO_DRAWDOWN = 0.20  # 20% max drawdown
MAX_DAILY_LOSS = 0.05  # 5% daily loss limit
MAX_EXPOSURE = 0.95    # 95% max portfolio exposure
VaR_CONFIDENCE = 0.95  # 95% VaR

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI AGENTS CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGENTS = {
    'market_observer': {
        'enabled': True,
        'scan_interval': 60,  # seconds
    },
    'strategy_generator': {
        'enabled': True,
        'population_size': 50,
        'generations': 5,
        'markets': ['crypto', 'forex', 'equities'],
        'timeframes': ['5m', '15m', '1h', '4h', '1d'],
        'concurrent_strategies': 6,
    },
    'rl_trader': {
        'enabled': True,
        'epsilon': 0.3,
        'learning_rate': 0.1,
    },
    'risk_enforcer': {
        'enabled': True,
        'max_position': POSITION_SIZE_MAX,
        'daily_loss_limit': MAX_DAILY_LOSS,
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BACKTESTING CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BACKTEST_CONFIG = {
    'walk_forward_train': 250,  # 250 days training
    'walk_forward_test': 50,    # 50 days testing
    'monte_carlo_sims': 1000,
    'monte_carlo_periods': 252,
    'overfit_threshold': 0.35,
}

# STRATEGY LAB CONFIG
STRATEGY_LAB = {
    'enable_grid_search': True,
    'grid_search_budget': 72,
    'objective': 'sharpe_with_drawdown_penalty',
    'risk_controls': {
        'max_position': POSITION_SIZE_MAX,
        'risk_per_trade': 0.01,
        'max_drawdown_stop': MAX_PORTFOLIO_DRAWDOWN,
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DASHBOARD SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DASHBOARD_PORT = 5011
DASHBOARD_HOST = "0.0.0.0"
REFRESH_INTERVAL = 5000  # milliseconds
THEME = "dark"

# V26 SMART CHART + BEHAVIOR ANALYTICS
V26_DASHBOARD_PORT = 5026
V26_SETTINGS = {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "history_limit": 220,
    "lookback_bos": 20,
    "lookback_choch": 12,
    "features": {
        "ema50": True,
        "ema200": True,
        "rsi": True,
        "macd": True,
        "bollinger": True,
        "volume": True,
        "structure": True,
        "bos": True,
        "choch": True,
        "depth": True,
        "volatility": True,
    },
    "exchanges": ["binance", "bybit", "kraken", "okx", "coinbase"],
    "trend_sources": ["amazon", "temu", "facebook_marketplace", "tiktok", "instagram", "x", "youtube"],
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMPLETE CONFIG DICT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIG = {
    'project_name': PROJECT_NAME,
    'version': VERSION,
    'root_dir': str(ROOT_DIR),
    'data_dir': str(DATA_DIR),
    'primary_exchange': PRIMARY_EXCHANGE,
    'exchanges': EXCHANGES,
    'symbols': TOP_SYMBOLS,
    'allocation': PORTFOLIO_ALLOCATION,
    'trading': {
        'mode': TRADING_MODE,
        'initial_capital': INITIAL_CAPITAL,
        'fee': TRADING_FEE,
        'slippage': SLIPPAGE,
    },
    'risk': {
        'max_drawdown': MAX_PORTFOLIO_DRAWDOWN,
        'max_daily_loss': MAX_DAILY_LOSS,
        'max_exposure': MAX_EXPOSURE,
    },
    'agents': AGENTS,
    'backtesting': BACKTEST_CONFIG,
    'strategy_lab': STRATEGY_LAB,
    'dashboard': {
        'port': DASHBOARD_PORT,
        'host': DASHBOARD_HOST,
        'refresh_interval': REFRESH_INTERVAL,
    },
    'v26': {
        'dashboard_port': V26_DASHBOARD_PORT,
        'settings': V26_SETTINGS,
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRINT CONFIG ON IMPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import json
    print(json.dumps({k: str(v) if not isinstance(v, dict) else v 
                     for k, v in CONFIG.items()}, indent=2))
