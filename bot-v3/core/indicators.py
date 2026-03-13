import pandas as pd
from core.logger import logger

def calculate_indicators(data):
    """Calcule les indicateurs techniques."""
    try:
        data["SMA20"] = data["Close"].rolling(20).mean()
        data["SMA50"] = data["Close"].rolling(50).mean()
        data["RSI"] = compute_rsi(data["Close"])
        data["MACD"], data["Signal"], data["Histogram"] = compute_macd(data["Close"])
        return data
    except Exception as e:
        logger.error(f"Erreur calcul indicateurs: {e}")
        return data

def compute_rsi(prices, period=14):
    """Calcule l'Indice de Force Relative (RSI)."""
    try:
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    except Exception as e:
        logger.error(f"Erreur RSI: {e}")
        return pd.Series([0] * len(prices))

def compute_macd(prices, fast=12, slow=26, signal=9):
    """Calcule le MACD (Moving Average Convergence Divergence)."""
    try:
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    except Exception as e:
        logger.error(f"Erreur MACD: {e}")
        return pd.Series([0] * len(prices)), pd.Series([0] * len(prices)), pd.Series([0] * len(prices))
