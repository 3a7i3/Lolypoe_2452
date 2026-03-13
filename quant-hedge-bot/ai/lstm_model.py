"""
LSTM Model - Modele LSTM pour time series prediction
"""

import numpy as np
from config import SEQUENCE_LENGTH, EPOCHS, BATCH_SIZE, LEARNING_RATE
from utils.logger import logger

class LSTMModel:
    """Modele LSTM pour les predictions."""
    
    def __init__(self):
        self.model = None
        self.history = None
    
    def build_model(self, input_shape):
        """Construit le modele LSTM."""
        try:
            import tensorflow as tf
            from tensorflow import keras
            from tensorflow.keras import layers
            
            self.model = keras.Sequential([
                layers.LSTM(50, activation='relu', input_shape=input_shape, return_sequences=True),
                layers.Dropout(0.2),
                layers.LSTM(50, activation='relu'),
                layers.Dropout(0.2),
                layers.Dense(25, activation='relu'),
                layers.Dense(1)
            ])
            
            self.model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                loss='mse',
                metrics=['mae']
            )
            
            logger.info("LSTM model built successfully")
            return self.model
        
        except ImportError:
            logger.warning("TensorFlow not installed. Skipping LSTM training.")
            return None
    
    def train(self, X_train, y_train, X_val, y_val):
        """Entraine le modele."""
        if self.model is None:
            logger.error("Model not built")
            return None
        
        try:
            self.history = self.model.fit(
                X_train, y_train,
                epochs=EPOCHS,
                batch_size=BATCH_SIZE,
                validation_data=(X_val, y_val),
                verbose=0
            )
            
            logger.info(f"LSTM training completed")
            return self.history
        
        except Exception as e:
            logger.error(f"Error training LSTM: {e}")
            return None
    
    def predict(self, X):
        """Fait une prediction."""
        if self.model is None:
            return None
        
        return self.model.predict(X, verbose=0)
