from core.market_data import get_data
from config import SYMBOLS, INTERVAL
from utils.logger import logger

def scan_market():
    """Scanne le marche pour tous les symboles."""
    market = {}
    
    for symbol in SYMBOLS:
        try:
            logger.info(f"Scan: {symbol}")
            data = get_data(symbol, interval=INTERVAL, period="1d")
            
            if data is not None and not data.empty:
                market[symbol] = data
            else:
                logger.warning(f"Pas de donnees pour {symbol}")
        except Exception as e:
            logger.error(f"Erreur scan {symbol}: {e}")
    
    return market
