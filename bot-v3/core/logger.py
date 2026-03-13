import logging
import csv
from datetime import datetime
from config import LOG_LEVEL, LOG_FILE

# Configure logger pour les logs
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

fh = logging.FileHandler(LOG_FILE)
fh.setLevel(LOG_LEVEL)

ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

def log_trade(signal, price=None):
    """Enregistre le trade dans CSV."""
    try:
        with open("data/trades.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                signal,
                price if price else "N/A"
            ])
        logger.info(f"Trade enregistre: {signal} @ {price}")
    except Exception as e:
        logger.error(f"Erreur enregistrement trade: {e}")
