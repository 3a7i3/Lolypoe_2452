"""
AI Predictor - Predictions de prix avec ML
"""

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from config import SEQUENCE_LENGTH, PREDICTION_HORIZON
from utils.logger import logger

class AIPredictor:
    """Prediit les prix avec machine learning."""
    
    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler()
        self.model_trained = False
    
    def predict_price(self, data, periods_ahead=5):
        """Predit le prix futur."""
        try:
            if len(data) < 50:
                logger.warning("Donnees insuffisantes pour prediction")
                return None
            
            # Preparer features
            df = data.copy()
            
            close_col = 'Close'
            if close_col not in df.columns:
                return None
            
            df['Return'] = df[close_col].pct_change()
            df['MA20'] = df[close_col].rolling(20).mean()
            df['MA50'] = df[close_col].rolling(50).mean()
            df['Volatility'] = df[close_col].rolling(20).std()
            df['RSI'] = self._calculate_rsi(df[close_col])
            
            df = df.dropna()
            
            if len(df) < 50:
                return None
            
            # Construire X et y
            feature_cols = [close_col, 'MA20', 'MA50', 'Volatility', 'RSI', 'Return']
            X = df[feature_cols].values
            y = df[close_col].shift(-1).values[:-1]
            X = X[:-1]
            
            # Normaliser
            X_scaled = self.scaler.fit_transform(X)
            
            # Entrainer
            self.model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
            self.model.fit(X_scaled, y)
            self.model_trained = True
            
            # Predictions
            last_data = X_scaled[-1].reshape(1, -1)
            predictions = []
            
            for _ in range(periods_ahead):
                pred = self.model.predict(last_data)[0]
                predictions.append(float(pred))
            
            logger.info(f"Predictions: {predictions}")
            return predictions
        
        except Exception as e:
            logger.error(f"Erreur prediction: {e}")
            return None
    
    def _calculate_rsi(self, prices, period=14):
        """Calcule RSI."""
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
