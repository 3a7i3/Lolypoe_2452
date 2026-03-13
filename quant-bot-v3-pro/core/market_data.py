import yfinance as yf
import pandas as pd
from utils.logger import logger
from config import LOOKBACK_PERIOD

def get_data(symbol, interval="1m", period="1d"):
    """Recupere les donnees de marche."""
    try:
        data = yf.download(
            tickers=symbol,
            interval=interval,
            period=period,
            progress=False
        )
        
        # Si vide
        if data is None or data.empty:
            logger.warning(f"Donnees vides pour {symbol}")
            return None
        
        # Flatten MultiIndex si present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Standardiser les colonnes
        data.columns = data.columns.str.upper()
        
        # Verifier les colonnes attendues
        required_cols = ['CLOSE', 'VOLUME']
        if not all(col in data.columns for col in required_cols):
            logger.warning(f"Colonnes manquantes pour {symbol}: {data.columns.tolist()}")
            return None
        
        return data
    except Exception as e:
        logger.error(f"Erreur fetching {symbol}: {e}")
        return None
