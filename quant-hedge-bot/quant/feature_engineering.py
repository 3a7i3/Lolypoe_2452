"""
Feature Engineering - Creation de features pour ML
"""

import pandas as pd
import numpy as np

class FeatureEngineering:
    """Cree des features engineered."""
    
    @staticmethod
    def create_features(data):
        """Cree l'ensemble complet de features."""
        data = data.copy()
        
        # Price-based
        FeatureEngineering.add_price_features(data)
        
        # Momentum
        FeatureEngineering.add_momentum_features(data)
        
        # Volatility
        FeatureEngineering.add_volatility_features(data)
        
        # Volume
        FeatureEngineering.add_volume_features(data)
        
        # Trend
        FeatureEngineering.add_trend_features(data)
        
        return data.dropna()
    
    @staticmethod
    def add_price_features(data):
        """Ajoute les features de prix."""
        data['Daily_Return'] = data['Close'].pct_change()
        data['Log_Return'] = np.log(data['Close'] / data['Close'].shift(1))
        data['High_Low_Range'] = (data['High'] - data['Low']) / data['Close']
        data['Close_Open_Range'] = (data['Close'] - data['Open']) / data['Close']
    
    @staticmethod
    def add_momentum_features(data):
        """Ajoute les features de momentum."""
        data['ROC_5'] = data['Close'].pct_change(5)
        data['ROC_10'] = data['Close'].pct_change(10)
        data['ROC_20'] = data['Close'].pct_change(20)
        data['Momentum_10'] = data['Close'] - data['Close'].shift(10)
        data['Momentum_20'] = data['Close'] - data['Close'].shift(20)
    
    @staticmethod
    def add_volatility_features(data):
        """Ajoute les features de volatilite."""
        data['Volatility_5'] = data['Close'].pct_change().rolling(5).std()
        data['Volatility_20'] = data['Close'].pct_change().rolling(20).std()
        data['Volatility_Ratio'] = data['Volatility_5'] / data['Volatility_20']
    
    @staticmethod
    def add_volume_features(data):
        """Ajoute les features de volume."""
        data['Volume_Change'] = data['Volume'].pct_change()
        data['Volume_MA_5'] = data['Volume'].rolling(5).mean()
        data['Volume_MA_20'] = data['Volume'].rolling(20).mean()
        data['Volume_Ratio'] = data['Volume'] / data['Volume_MA_20']
    
    @staticmethod
    def add_trend_features(data):
        """Ajoute les features de tendance."""
        data['SMA_5'] = data['Close'].rolling(5).mean()
        data['SMA_10'] = data['Close'].rolling(10).mean()
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['EMA_12'] = data['Close'].ewm(span=12).mean()
        data['Price_Above_SMA20'] = (data['Close'] > data['SMA_20']).astype(int)
