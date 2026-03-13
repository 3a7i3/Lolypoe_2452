"""
Price Predictor - AI-powered price prediction
"""

import logging
from typing import Dict, Optional
import numpy as np
import config
from .feature_engineering import FeatureEngineer
from .model_trainer import ModelTrainer

logger = logging.getLogger(__name__)

class PricePredictor:
    """AI-powered price prediction"""
    
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.model_trainer = ModelTrainer()
        self.models = {}
        logger.info("✓ Price Predictor initialized")
    
    async def predict(self, symbol: str) -> Optional[Dict]:
        """
        Predict future price for a symbol
        Returns: prediction with confidence
        """
        try:
            # Simulate prediction
            prediction_confidence = np.random.uniform(0.5, 0.95)
            predicted_price = 100.0 * (1 + np.random.uniform(-0.05, 0.05))
            
            prediction = {
                'symbol': symbol,
                'predicted_price': predicted_price,
                'confidence': prediction_confidence,
                'timeframe': config.PREDICTION_WINDOW,
                'direction': 'UP' if predicted_price > 100 else 'DOWN'
            }
            
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction error for {symbol}: {e}")
            return None
    
    async def predict_batch(self, symbols: list) -> Dict:
        """
        Predict prices for multiple symbols
        Returns: dict of predictions
        """
        try:
            predictions = {}
            
            for symbol in symbols:
                pred = await self.predict(symbol)
                if pred:
                    predictions[symbol] = pred
            
            return predictions
            
        except Exception as e:
            logger.error(f"Batch prediction error: {e}")
            return {}
    
    def train_predictor(self, symbol: str, ohlcv_data: list) -> bool:
        """
        Train predictor for a symbol
        Returns: success
        """
        try:
            if len(ohlcv_data) < config.LSTM_SEQUENCE_LENGTH + 10:
                logger.warning(f"Insufficient data for {symbol}")
                return False
            
            # Create features
            features = self.feature_engineer.create_features(ohlcv_data)
            labels = self.feature_engineer.create_labels(ohlcv_data)
            
            if not features or not labels:
                return False
            
            # Train models
            logger.info(f"Training predictor for {symbol}...")
            
            # Train Random Forest
            if len(labels) > 0:
                X = np.array([features]).reshape(1, -1)
                y = np.array([labels[0]])
                
                self.model_trainer.train_random_forest(X, y)
            
            return True
            
        except Exception as e:
            logger.error(f"Predictor training error: {e}")
            return False
