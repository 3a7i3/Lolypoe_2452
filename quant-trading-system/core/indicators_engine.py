"""
Indicators Engine - Calculate technical indicators
"""

import logging
from typing import Dict, List
import pandas as pd
import numpy as np
import config

logger = logging.getLogger(__name__)

class IndicatorsEngine:
    """Calculate technical indicators"""
    
    @staticmethod
    async def calculate(symbol: str, market_data: Dict) -> Dict:
        """
        Calculate all technical indicators
        Returns: dict with all indicators
        """
        try:
            indicators = {}
            
            # Extract prices (simulated)
            prices = market_data.get('prices', [])
            if len(prices) < 200:
                return indicators
            
            # Moving Averages
            indicators['sma_20'] = IndicatorsEngine.sma(prices, 20)
            indicators['sma_50'] = IndicatorsEngine.sma(prices, 50)
            indicators['sma_200'] = IndicatorsEngine.sma(prices, 200)
            indicators['ema_12'] = IndicatorsEngine.ema(prices, 12)
            indicators['ema_26'] = IndicatorsEngine.ema(prices, 26)
            
            # Momentum
            indicators['rsi_14'] = IndicatorsEngine.rsi(prices, 14)
            indicators['macd'] = IndicatorsEngine.macd(prices)
            
            # Volatility
            indicators['atr_14'] = IndicatorsEngine.atr(prices, 14)
            indicators['bb_20'] = IndicatorsEngine.bollinger_bands(prices, 20)
            
            # Trend
            indicators['adx_14'] = IndicatorsEngine.adx(prices, 14)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            return {}
    
    @staticmethod
    def sma(prices: List, period: int) -> float:
        """Simple Moving Average"""
        if len(prices) < period:
            return 0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def ema(prices: List, period: int) -> float:
        """Exponential Moving Average"""
        if len(prices) < period:
            return 0
        
        k = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = price * k + ema * (1 - k)
        
        return ema
    
    @staticmethod
    def rsi(prices: List, period: int = 14) -> float:
        """Relative Strength Index"""
        if len(prices) < period:
            return 50
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        seed = deltas[:period]
        
        up = sum([x for x in seed if x > 0]) / period
        down = sum([abs(x) for x in seed if x < 0]) / period
        
        rs = up / down if down != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def macd(prices: List) -> Dict:
        """MACD Indicator"""
        if len(prices) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema12 = IndicatorsEngine.ema(prices, 12)
        ema26 = IndicatorsEngine.ema(prices, 26)
        
        macd = ema12 - ema26
        signal = ema12 * 0.33 + ema26 * 0.67  # Simplified
        histogram = macd - signal
        
        return {'macd': macd, 'signal': signal, 'histogram': histogram}
    
    @staticmethod
    def atr(prices: List, period: int = 14) -> float:
        """Average True Range"""
        if len(prices) < period:
            return 0
        
        # Simplified ATR
        recent = prices[-period:]
        return (max(recent) - min(recent)) / 2
    
    @staticmethod
    def bollinger_bands(prices: List, period: int = 20, std_dev: int = 2) -> Dict:
        """Bollinger Bands"""
        if len(prices) < period:
            return {'upper': 0, 'middle': 0, 'lower': 0}
        
        recent = prices[-period:]
        middle = sum(recent) / period
        std = np.std(recent)
        
        return {
            'upper': middle + (std * std_dev),
            'middle': middle,
            'lower': middle - (std * std_dev)
        }
    
    @staticmethod
    def adx(prices: List, period: int = 14) -> float:
        """Average Directional Index"""
        # Simplified ADX
        return 50  # Neutral by default
