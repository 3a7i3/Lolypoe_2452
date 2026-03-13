# Configuration pour le bot crypto v3

# Symbols
SYMBOLS = ["BTC-USD", "ETH-USD", "BNB-USD"]

# Data fetching
TIMEFRAME = "1h"
LIMIT = 200

# Strategie
RSI_LOWER = 30
RSI_UPPER = 70
MA_SHORT = 20
MA_LONG = 50

# Risk Management
MAX_TRADES = 5
MAX_POSITION_SIZE = 0.1
STOP_LOSS_PCT = 2
TAKE_PROFIT_PCT = 5

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "data/bot.log"
