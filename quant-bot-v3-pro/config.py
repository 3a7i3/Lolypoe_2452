# ==========================================
# QUANT BOT v3 PRO - Configuration
# ==========================================

# Trading symbols
SYMBOLS = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "BNB-USD"
]

# Data collection
INTERVAL = "1m"
LOOKBACK_PERIOD = 200

# Capital & Risk
CAPITAL = 10000
RISK_PER_TRADE = 0.02  # 2% per trade
MAX_POSITION_SIZE = 0.1  # 10% of capital

# Strategy
RSI_LOWER = 30
RSI_UPPER = 70
MA_SHORT = 20
MA_LONG = 50

# Logging
LOG_FILE = "data/bot.log"
LOG_LEVEL = "INFO"

# Cache
CACHE_DIR = "data/market_cache"
