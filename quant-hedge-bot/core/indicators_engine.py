"""
Indicators Engine - Tous les indicateurs techniques
"""

import pandas as pd
import numpy as np
from config import SMA_SHORT, SMA_LONG, RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL
from config import BOLLINGER_PERIOD, BOLLINGER_STD
from utils.logger import logger

class IndicatorsEngine:
    """Calcule les indicateurs techniques."""
    
    @staticmethod
    def add_all_indicators(data):
        """Ajoute tous les indicateurs."""
        data = data.copy()
        
        # Moving Averages
        data['SMA_20'] = IndicatorsEngine.calculate_sma(data['Close'], 20)
        data['SMA_50'] = IndicatorsEngine.calculate_sma(data['Close'], 50)
        data['SMA_200'] = IndicatorsEngine.calculate_sma(data['Close'], 200)
        data['EMA_12'] = IndicatorsEngine.calculate_ema(data['Close'], 12)
        data['EMA_26'] = IndicatorsEngine.calculate_ema(data['Close'], 26)
        
        # Momentum
        data['RSI'] = IndicatorsEngine.calculate_rsi(data['Close'], RSI_PERIOD)
        data['MACD'], data['MACD_Signal'], data['MACD_Hist'] = IndicatorsEngine.calculate_macd(data['Close'])
        
        # Volatility
        data['ATR'] = IndicatorsEngine.calculate_atr(data)
        data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = IndicatorsEngine.calculate_bollinger(data['Close'])
        
        # Volume
        data['OBV'] = IndicatorsEngine.calculate_obv(data)
        data['VWAP'] = IndicatorsEngine.calculate_vwap(data)
        
        # Trend
        data['ADX'] = IndicatorsEngine.calculate_adx(data)
        
        return data.dropna()
    
    @staticmethod
    def calculate_sma(prices, period):
        """Simple Moving Average."""
        return prices.rolling(period).mean()
    
    @staticmethod
    def calculate_ema(prices, period):
        """Exponential Moving Average."""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Relative Strength Index."""
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """MACD: Moving Average Convergence Divergence."""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_histogram = macd - macd_signal
        
        return macd, macd_signal, macd_histogram
    
    @staticmethod
    def calculate_atr(data, period=14):
        """Average True Range."""
        high_low = data['High'] - data['Low']
        high_close = abs(data['High'] - data['Close'].shift(1))
        low_close = abs(data['Low'] - data['Close'].shift(1))
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr
    
    @staticmethod
    def calculate_bollinger(prices, period=20, std_dev=2):
        """Bollinger Bands."""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        
        bb_upper = sma + (std_dev * std)
        bb_lower = sma - (std_dev * std)
        
        return bb_upper, sma, bb_lower
    
    @staticmethod
    def calculate_obv(data):
        """On-Balance Volume."""
        obv = pd.Series(index=data.index, dtype=float)
        obv.iloc[0] = data['Volume'].iloc[0]
        
        for i in range(1, len(data)):
            if data['Close'].iloc[i] > data['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + data['Volume'].iloc[i]
            elif data['Close'].iloc[i] < data['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - data['Volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def calculate_vwap(data):
        """Volume Weighted Average Price."""
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        vwap = (typical_price * data['Volume']).cumsum() / data['Volume'].cumsum()
        return vwap
    
    @staticmethod
    def calculate_adx(data, period=14):
        """Average Directional Index."""
        high_diff = data['High'].diff()
        low_diff = -data['Low'].diff()
        
        dm_plus = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        dm_minus = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        tr = IndicatorsEngine.calculate_atr(data, 1)
        
        atr_sum = tr.rolling(period).sum()
        dm_plus_sum = dm_plus.rolling(period).sum()
        dm_minus_sum = dm_minus.rolling(period).sum()
        
        di_plus = 100 * dm_plus_sum / atr_sum
        di_minus = 100 * dm_minus_sum / atr_sum
        
        di_diff = abs(di_plus - di_minus)
        di_sum = di_plus + di_minus
        
        dx = 100 * di_diff / di_sum
        adx = dx.rolling(period).mean()
        
        return adx
