import pandas as pd
from core.indicators import add_indicators
from utils.logger import logger
from config import RSI_LOWER, RSI_UPPER, MA_SHORT, MA_LONG

def generate_trade_signal(data):
    """
    Genere un signal de trading avec SMA + RSI + MACD.
    
    Strategie:
    - BUY: SMA20 > SMA50 + RSI < 70 + MACD > Signal
    - SELL: SMA20 < SMA50 + RSI > 30 + MACD < Signal
    """
    try:
        if data is None or data.empty or len(data) < 50:
            return "HOLD"
        
        df = add_indicators(data)
        
        last_idx = len(df) - 1
        last = df.iloc[last_idx]
        
        # Verifier les NaN
        if pd.isna(last["RSI"]) or pd.isna(last["SMA20"]) or pd.isna(last["SMA50"]) or \
           pd.isna(last.get("MACD")) or pd.isna(last.get("Signal")):
            return "HOLD"
        
        sma20 = float(last["SMA20"])
        sma50 = float(last["SMA50"])
        rsi = float(last["RSI"])
        macd = float(last.get("MACD", 0))
        signal_line = float(last.get("Signal", 0))
        
        # Conditions technique
        sma_bullish = sma20 > sma50
        sma_bearish = sma20 < sma50
        
        rsi_not_overbought = rsi < 70
        rsi_not_oversold = rsi > 30
        
        macd_bullish = macd > signal_line
        macd_bearish = macd < signal_line
        
        # BUY: Multi-indicators confirmation
        if sma_bullish and rsi_not_overbought and macd_bullish:
            logger.debug(f"BUY signal: SMA20={sma20:.2f}, SMA50={sma50:.2f}, RSI={rsi:.2f}, MACD={macd:.4f}")
            return "BUY"
        
        # SELL: Multi-indicators confirmation
        if sma_bearish and rsi_not_oversold and macd_bearish:
            logger.debug(f"SELL signal: SMA20={sma20:.2f}, SMA50={sma50:.2f}, RSI={rsi:.2f}, MACD={macd:.4f}")
            return "SELL"
        
        return "HOLD"
    except Exception as e:
        logger.error(f"Erreur generation signal: {e}")
        return "HOLD"
