"""
Logger Utility - Quant Hedge Bot
=================================
Logging centralisé avec fichiers et console
"""

import logging
import os
from datetime import datetime
from config import LOG_DIR, LOG_FILE, LOG_LEVEL

# Créer le dossier logs s'il n'existe pas
os.makedirs(LOG_DIR, exist_ok=True)

# Configuration du logger
logger = logging.getLogger('quant_hedge_bot')
logger.setLevel(getattr(logging, LOG_LEVEL))

# Format
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Handler pour fichier
file_handler = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler pour console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def log_trade(signal, symbol, price, quantity, reason=""):
    """Enregistre un trade."""
    logger.info(f"[TRADE] {signal} {symbol} x{quantity} @ ${price:.2f} - {reason}")

def log_position(symbol, size, entry_price, current_price, pnl_percent):
    """Enregistre une position."""
    logger.info(f"[POSITION] {symbol}: ${entry_price:.2f} -> ${current_price:.2f} | PnL: {pnl_percent:.2f}%")

def log_risk_event(event_type, description):
    """Enregistre un événement de risque."""
    logger.warning(f"[RISK] {event_type}: {description}")

def log_backtest_result(metric, value):
    """Enregistre un résultat de backtest."""
    logger.info(f"[BACKTEST] {metric}: {value}")
