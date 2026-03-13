"""
Model Trainer - Train and manage ML models
"""

import logging
import pickle
from typing import Dict, Tuple
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import config

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available")

class ModelTrainer:
    """Train and manage ML models"""
    
    def __init__(self):
        self.random_forest = None
        self.lstm_model = None
        self.scaler = StandardScaler()
        logger.info("✓ Model Trainer initialized")
    
    def train_random_forest(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict:
        """
        Train Random Forest model
        Returns: model and metrics
        """
        try:
            logger.info("Training Random Forest...")
            
            self.random_forest = RandomForestRegressor(
                n_estimators=config.RF_N_ESTIMATORS,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            self.random_forest.fit(X_train, y_train)
            
            score = self.random_forest.score(X_train, y_train)
            logger.info(f"✓ Random Forest trained. R² Score: {score:.4f}")
            
            return {
                'model': self.random_forest,
                'score': score,
                'n_features': self.random_forest.n_features_in_
            }
            
        except Exception as e:
            logger.error(f"Random Forest training error: {e}")
            return {}
    
    def train_lstm(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict:
        """
        Train LSTM model
        Returns: model and metrics
        """
        try:
            if not TENSORFLOW_AVAILABLE:
                logger.warning("LSTM training not available (TensorFlow not installed)")
                return {}
            
            logger.info("Training LSTM...")
            
            # Reshape for LSTM [samples, timesteps, features]
            X_train = X_train.reshape((X_train.shape[0], config.LSTM_SEQUENCE_LENGTH, 1))
            
            self.lstm_model = keras.Sequential([
                keras.layers.LSTM(64, activation='relu', input_shape=(config.LSTM_SEQUENCE_LENGTH, 1)),
                keras.layers.Dropout(0.2),
                keras.layers.Dense(32, activation='relu'),
                keras.layers.Dense(1)
            ])
            
            self.lstm_model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            
            history = self.lstm_model.fit(
                X_train, y_train,
                epochs=config.LSTM_EPOCHS,
                batch_size=config.LSTM_BATCH_SIZE,
                verbose=0,
                validation_split=0.2
            )
            
            logger.info(f"✓ LSTM trained. Final loss: {history.history['loss'][-1]:.4f}")
            
            return {
                'model': self.lstm_model,
                'history': history,
                'final_loss': history.history['loss'][-1]
            }
            
        except Exception as e:
            logger.error(f"LSTM training error: {e}")
            return {}
    
    def predict_rf(self, X: np.ndarray) -> np.ndarray:
        """Predict with Random Forest"""
        try:
            if self.random_forest is None:
                return np.array([])
            return self.random_forest.predict(X)
        except Exception as e:
            logger.error(f"RF prediction error: {e}")
            return np.array([])
    
    def predict_lstm(self, X: np.ndarray) -> np.ndarray:
        """Predict with LSTM"""
        try:
            if not TENSORFLOW_AVAILABLE or self.lstm_model is None:
                return np.array([])
            
            X = X.reshape((X.shape[0], config.LSTM_SEQUENCE_LENGTH, 1))
            return self.lstm_model.predict(X, verbose=0)
            
        except Exception as e:
            logger.error(f"LSTM prediction error: {e}")
            return np.array([])
    
    def save_model(self, model_name: str, filepath: str) -> bool:
        """Save trained model"""
        try:
            if model_name == 'rf' and self.random_forest:
                with open(filepath, 'wb') as f:
                    pickle.dump(self.random_forest, f)
                logger.info(f"Random Forest saved to {filepath}")
                return True
            
            elif model_name == 'lstm' and self.lstm_model and TENSORFLOW_AVAILABLE:
                self.lstm_model.save(filepath)
                logger.info(f"LSTM saved to {filepath}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Model save error: {e}")
            return False
    
    def load_model(self, model_name: str, filepath: str) -> bool:
        """Load trained model"""
        try:
            if model_name == 'rf':
                with open(filepath, 'rb') as f:
                    self.random_forest = pickle.load(f)
                logger.info(f"Random Forest loaded from {filepath}")
                return True
            
            elif model_name == 'lstm' and TENSORFLOW_AVAILABLE:
                self.lstm_model = keras.models.load_model(filepath)
                logger.info(f"LSTM loaded from {filepath}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Model load error: {e}")
            return False
