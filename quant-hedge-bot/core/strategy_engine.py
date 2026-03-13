"""
Strategy Engine - Generation de signaux de trading
"""

import pandas as pd
from config import SMA_SHORT, SMA_LONG, RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT
from utils.logger import logger

class StrategyEngine:
    """Genere les signaux de trading."""
    
    @staticmethod
    def generate_signal(data):
        """Genere un signal de trading multi-indicateurs."""
        if len(data) < 50:
            return "HOLD"
        
        try:
            last = data.iloc[-1]
            
            # Conditions SMA
            sma_bullish = last['SMA_20'] > last['SMA_50'] > last['SMA_200']
            sma_bearish = last['SMA_20'] < last['SMA_50'] < last['SMA_200']
            
            # Conditions RSI
            rsi_oversold = last['RSI'] < RSI_OVERSOLD
            rsi_overbought = last['RSI'] > RSI_OVERBOUGHT
            
            # Conditions MACD
            macd_bullish = last['MACD'] > last['MACD_Signal']
            macd_bearish = last['MACD'] < last['MACD_Signal']
            
            # Conditions Bollinger
            bb_top = last['Close'] > last['BB_Upper']
            bb_bottom = last['Close'] < last['BB_Lower']
            
            # Signaux composites
            buy_signal = (
                sma_bullish and 
                not rsi_overbought and 
                macd_bullish and 
                not bb_top
            )
            
            sell_signal = (
                sma_bearish and 
                not rsi_oversold and 
                macd_bearish and 
                not bb_bottom
            )
            
            if buy_signal:
                return "BUY"
            elif sell_signal:
                return "SELL"
            else:
                return "HOLD"
        
        except Exception as e:
            logger.error(f"Erreur generation signal: {e}")
            return "HOLD"
    
    @staticmethod
    def generate_signal_with_confidence(data):
        """Genere un signal avec score de confiance."""
        signal = StrategyEngine.generate_signal(data)
        confidence = StrategyEngine.calculate_signal_confidence(data)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'indicators': StrategyEngine.get_indicator_values(data)
        }
    
    @staticmethod
    def calculate_signal_confidence(data):
        """Calcule la confiance du signal (0-1)."""
        if data.empty:
            return 0.0
        
        try:
            last = data.iloc[-1]
            
            # Compter les confirmations
            confirmations = 0
            
            if last['SMA_20'] > last['SMA_50']:
                confirmations += 1
            if last['RSI'] > 30 and last['RSI'] < 70:
                confirmations += 1
            if last['MACD'] > last['MACD_Signal']:
                confirmations += 1
            if last['ADX'] > 25:
                confirmations += 1
            
            confidence = confirmations / 4.0
            return confidence
        
        except Exception as e:
            return 0.5
    
    @staticmethod
    def get_indicator_values(data):
        """Retourne les valeurs des indicateurs."""
        if data.empty:
            return {}
        
        last = data.iloc[-1]
        return {
            'close': float(last['Close']),
            'sma_20': float(last['SMA_20']),
            'sma_50': float(last['SMA_50']),
            'rsi': float(last['RSI']),
            'macd': float(last['MACD']),
            'atr': float(last['ATR']),
            'volume': float(last['Volume'])
        }
