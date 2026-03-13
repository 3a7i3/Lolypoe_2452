import pandas as pd
from utils.logger import logger

def add_indicators(df):
    """Ajoute les indicateurs techniques au DataFrame."""
    try:
        df = df.copy()
        
        # SMA
        df["SMA20"] = df["CLOSE"].rolling(20).mean()
        df["SMA50"] = df["CLOSE"].rolling(50).mean()
        
        # RSI
        df["RSI"] = compute_rsi(df)
        
        return df
    except Exception as e:
        logger.error(f"Erreur calcul indicateurs: {e}")
        return df

def compute_rsi(df, period=14):
    """Calcule l'Indice de Force Relative (RSI)."""
    try:
        delta = df["CLOSE"].diff()
        
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        
        rs = avg_gain / avg_loss
        
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    except Exception as e:
        logger.error(f"Erreur RSI: {e}")
        return pd.Series([0] * len(df))
