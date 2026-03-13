import csv
from datetime import datetime
from utils.logger import logger
from utils.notifier import notify_trade
from core.risk_manager import increment_trade_count

def execute_trade(symbol, signal, price=None):
    """Execute un trade et l'enregistre."""
    try:
        log_entry = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            signal,
            price if price else "N/A"
        ]
        
        # Enregistrer dans CSV
        with open("data/trades.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(log_entry)
        
        if price:
            logger.info(f"Trade execute: {symbol} {signal} @ ${price:.2f}")
            notify_trade(symbol, signal, price)
            print(f"[EXECUTE] {symbol} -> {signal} @ ${price:.2f}")
        else:
            logger.info(f"Trade execute: {symbol} {signal}")
            print(f"[EXECUTE] {symbol} -> {signal}")
        
        increment_trade_count()
    except Exception as e:
        logger.error(f"Erreur execution trade: {e}")
