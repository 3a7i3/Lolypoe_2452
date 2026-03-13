"""
System Configuration
"""

import os
from typing import Dict, Any

# API Configuration
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', 8000))
API_WORKERS = int(os.getenv('API_WORKERS', 4))

# Market Scanner Configuration
SCANNER_CONFIG = {
    'min_volume_usd': 100000,
    'max_symbols': 100,
    'scan_interval_seconds': 60,
    'top_crypto_limit': 50
}

# Portfolio Configuration
PORTFOLIO_CONFIG = {
    'initial_capital': 100000,
    'max_positions': 20,
    'max_position_size': 0.10,  # 10% per position
    'max_drawdown': 0.25,  # 25% max drawdown
    'rebalance_frequency': 'daily'  # 'hourly', 'daily', 'weekly'
}

# Risk Management Configuration
RISK_CONFIG = {
    'max_daily_loss': 0.05,  # 5% max daily loss
    'max_position_risk': 0.02,  # 2% per position
    'stop_loss_percent': 0.10,  # 10% stop loss
    'take_profit_percent': 0.30,  # 30% take profit
    'risk_free_rate': 0.02
}

# Strategy Generation Configuration
STRATEGY_CONFIG = {
    'population_size': 50,
    'top_k_strategies': 5,
    'generation_frequency': 'hourly',  # How often to generate new strategies
    'min_trade_signals': 10  # Minimum signals before evaluation
}

# Backtester Configuration
BACKTEST_CONFIG = {
    'initial_capital': 100000,
    'commission_rate': 0.001,  # 0.1%
    'slippage_percent': 0.0001,  # 0.01%
    'in_sample_size': 0.6,
    'out_sample_size': 0.2,
    'monte_carlo_simulations': 100
}

# Machine Learning Configuration
ML_CONFIG = {
    'lstm_lookback': 60,
    'lstm_forecast_steps': 5,
    'rl_learning_rate': 0.001,
    'rl_gamma': 0.95,
    'rl_epsilon': 1.0,
    'batch_size': 32
}

# Execution Configuration
EXECUTION_CONFIG = {
    'order_timeout_seconds': 30,
    'partial_fill_enabled': True,
    'max_orders_per_symbol': 3,
    'order_type': 'market'  # 'market', 'limit', 'stop'
}

# Data Configuration
DATA_CONFIG = {
    'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
    'history_lookback_days': 365,
    'cache_enabled': True,
    'cache_ttl_seconds': 3600
}

# Exchange Configuration
EXCHANGE_CONFIG = {
    'binance': {
        'enabled': True,
        'api_key': os.getenv('BINANCE_API_KEY', ''),
        'api_secret': os.getenv('BINANCE_API_SECRET', '')
    },
    'bybit': {
        'enabled': True,
        'api_key': os.getenv('BYBIT_API_KEY', ''),
        'api_secret': os.getenv('BYBIT_API_SECRET', '')
    },
    'coinbase': {
        'enabled': True,
        'api_key': os.getenv('COINBASE_API_KEY', ''),
        'passphrase': os.getenv('COINBASE_PASSPHRASE', '')
    },
    'kraken': {
        'enabled': True,
        'api_key': os.getenv('KRAKEN_API_KEY', ''),
        'api_secret': os.getenv('KRAKEN_API_SECRET', '')
    }
}

# System Configuration
SYSTEM_CONFIG = {
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'debug_mode': os.getenv('DEBUG_MODE', 'False').lower() == 'true',
    'live_trading': os.getenv('LIVE_TRADING', 'False').lower() == 'true',
    'paper_trading': not os.getenv('LIVE_TRADING', 'False').lower() == 'true',
    'heartbeat_interval_seconds': 60,
    'max_retries': 3,
    'retry_delay_seconds': 5
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    'email_enabled': False,
    'email_address': os.getenv('EMAIL_ADDRESS', ''),
    'discord_enabled': True,
    'discord_webhook': os.getenv('DISCORD_WEBHOOK', ''),
    'telegram_enabled': False,
    'telegram_token': os.getenv('TELEGRAM_TOKEN', ''),
    'slack_enabled': False,
    'slack_webhook': os.getenv('SLACK_WEBHOOK', '')
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'port': 5006,
    'host': '0.0.0.0',
    'refresh_interval_ms': 5000,
    'theme': 'dark',
    'enable_realtime': True
}

# Performance Monitoring
MONITORING_CONFIG = {
    'track_metrics': True,
    'metrics_interval_seconds': 300,  # 5 minutes
    'enable_profiling': False,
    'memory_limit_mb': 2048
}

# Strategy Parameters (can be tuned)
STRATEGY_PARAMETERS = {
    'rsi_period': (7, 21),
    'macd_fast': (8, 15),
    'macd_slow': (20, 35),
    'bollinger_period': (15, 30),
    'bollinger_std': (1.5, 2.5),
    'atr_period': (10, 20),
    'sma_short': (5, 20),
    'sma_long': (40, 100)
}


def get_config() -> Dict[str, Any]:
    """Get full system configuration"""
    return {
        'api': API_HOST,
        'port': API_PORT,
        'scanner': SCANNER_CONFIG,
        'portfolio': PORTFOLIO_CONFIG,
        'risk': RISK_CONFIG,
        'strategy': STRATEGY_CONFIG,
        'backtest': BACKTEST_CONFIG,
        'ml': ML_CONFIG,
        'execution': EXECUTION_CONFIG,
        'data': DATA_CONFIG,
        'exchanges': EXCHANGE_CONFIG,
        'system': SYSTEM_CONFIG,
        'notifications': NOTIFICATION_CONFIG,
        'dashboard': DASHBOARD_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'strategy_parameters': STRATEGY_PARAMETERS
    }


def get_trading_symbols() -> list:
    """Get list of tradeable symbols"""
    return [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT',
        'XRP/USDT', 'DOGE/USDT', 'AVAX/USDT', 'LINK/USDT', 'MATIC/USDT',
        'UNI/USDT', 'XLM/USDT', 'LTC/USDT', 'ATOM/USDT', 'ARB/USDT',
        'OP/USDT', 'APT/USDT', 'BLUR/USDT', 'FIT/USDT', 'FTT/USDT'
    ]
