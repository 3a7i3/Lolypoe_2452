import pandas as pd
from core.logger import logger

def generate_signal(data):
    """
    Genere un signal de trading base sur SMA + RSI + MACD.
    
    Strategie:
    - BUY: SMA20 > SMA50 + RSI < 70 + MACD > Signal
    - SELL: SMA20 < SMA50 + RSI > 30 + MACD < Signal
    """
    try:
        if data.empty or len(data) < 50:
            return "HOLD"
        
        # Obtenir la derniere ligne
        last_idx = len(data) - 1
        
        sma20 = data['SMA20'].iloc[last_idx]
        sma50 = data['SMA50'].iloc[last_idx]
        rsi = data['RSI'].iloc[last_idx]
        macd = data['MACD'].iloc[last_idx]
        signal_line = data['Signal'].iloc[last_idx]
        
        # Verifier les NaN
        if pd.isna(sma20) or pd.isna(sma50) or pd.isna(rsi) or pd.isna(macd):
            return "HOLD"
        
        # Convertir en float
        sma20 = float(sma20)
        sma50 = float(sma50)
        rsi = float(rsi)
        macd = float(macd)
        signal_line = float(signal_line)
        
        # Logique de signal amelioree
        sma_bullish = sma20 > sma50
        sma_bearish = sma20 < sma50
        
        rsi_oversold = rsi < 30
        rsi_overbought = rsi > 70
        
        macd_bullish = macd > signal_line
        macd_bearish = macd < signal_line
        
        # BUY: Confirmation multi-indicateurs
        if sma_bullish and not rsi_overbought and macd_bullish:
            logger.debug(f"Signal BUY: SMA={sma20:.2f}>{sma50:.2f}, RSI={rsi:.2f}, MACD={macd:.4f}")
            return "BUY"
        
        # SELL: Confirmation multi-indicateurs
        if sma_bearish and not rsi_oversold and macd_bearish:
            logger.debug(f"Signal SELL: SMA={sma20:.2f}<{sma50:.2f}, RSI={rsi:.2f}, MACD={macd:.4f}")
            return "SELL"
        
        # HOLD par defaut
        return "HOLD"
    except Exception as e:
        logger.error(f"Erreur generation signal: {e}")
        return "HOLD"
