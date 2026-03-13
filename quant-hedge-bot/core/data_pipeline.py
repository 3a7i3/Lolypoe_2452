"""
Data Pipeline - Preparation et nettoyage des donnees
"""

import pandas as pd
import numpy as np
from config import LOOKBACK_PERIOD
from utils.logger import logger

class DataPipeline:
    """Traite et prepare les donnees."""
    
    @staticmethod
    def clean_data(data):
        """Nettoie les donnees."""
        # Supprimer les NaN
        data = data.dropna()
        
        # Supprimer les doublons
        data = data[~data.index.duplicated(keep='first')]
        
        # Verifier les colonnes
        required_cols = ['Close', 'High', 'Low', 'Volume']
        for col in required_cols:
            if col not in data.columns:
                logger.warning(f"Colonne manquante: {col}")
                return None
        
        return data
    
    @staticmethod
    def resample_data(data, interval='1h'):
        """Reechantillonne les donnees."""
        try:
            return data.resample(interval).agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
        except Exception as e:
            logger.error(f"Erreur resampling: {e}")
            return data
    
    @staticmethod
    def normalize_features(data):
        """Normalise les features pour ML."""
        scaler_data = data[['Close', 'Volume']].copy()
        
        # Min-max scale
        for col in scaler_data.columns:
            min_val = scaler_data[col].min()
            max_val = scaler_data[col].max()
            if max_val - min_val != 0:
                scaler_data[col] = (scaler_data[col] - min_val) / (max_val - min_val)
        
        return scaler_data
    
    @staticmethod
    def add_features(data):
        """Ajoute des features engineered."""
        data = data.copy()
        
        # Returns
        data['Returns'] = data['Close'].pct_change()
        data['Log_Returns'] = np.log(data['Close'] / data['Close'].shift(1))
        
        # Volatility
        data['Volatility'] = data['Returns'].rolling(20).std()
        data['HV'] = data['Log_Returns'].rolling(20).std() * np.sqrt(252)  # Annualized
        
        # Volume changes
        data['Volume_Change'] = data['Volume'].pct_change()
        data['Volume_MA'] = data['Volume'].rolling(20).mean()
        
        # Price features
        data['Daily_Range'] = (data['High'] - data['Low']) / data['Close']
        data['High_Low_Ratio'] = data['High'] / data['Low']
        
        # Momentum
        data['Price_Momentum'] = (data['Close'] - data['Close'].shift(10)) / data['Close'].shift(10)
        
        return data.dropna()
    
    @staticmethod
    def create_sequences(data, seq_length=60):
        """Cree des sequences pour LSTM."""
        sequences = []
        targets = []
        
        for i in range(len(data) - seq_length):
            seq = data.iloc[i:i+seq_length].values
            target = data.iloc[i+seq_length][0]  # Close price
            sequences.append(seq)
            targets.append(target)
        
        return np.array(sequences), np.array(targets)
