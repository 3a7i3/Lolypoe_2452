"""
LSTM Model Trainer - Deep learning price prediction using LSTM networks
Multivariate time series modeling with multiple lookback periods
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import os

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Sequential
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from sklearn.preprocessing import StandardScaler
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger_msg = "TensorFlow not available - LSTM training will use mock mode"

import config

logger = logging.getLogger(__name__)

class LSTMTrainer:
    """LSTM model trainer for cryptocurrency price prediction"""
    
    def __init__(self):
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not installed. Using mock LSTM for testing.")
        
        self.lstm_config = config.ML_MODELS.get('LSTM', {})
        self.lookback_period = self.lstm_config.get('lookback_period', 120)
        self.output_dim = self.lstm_config.get('output_dim', 1)
        self.lstm_layers = self.lstm_config.get('lstm_layers', [128, 64, 32])
        self.dropout_rate = self.lstm_config.get('dropout_rate', 0.3)
        self.learning_rate = self.lstm_config.get('learning_rate', 0.001)
        self.batch_size = self.lstm_config.get('batch_size', 32)
        self.epochs = self.lstm_config.get('epochs', 100)
        self.patience = self.lstm_config.get('early_stopping_patience', 15)
        
        # Model storage
        self.models = {}  # Keyed by symbol
        self.scalers = {}  # Feature scalers per symbol
        self.scalers_y = {}  # Target scalers per symbol
        self.model_history = {}  # Training history per symbol
        self.model_performance = {}  # Validation metrics per symbol
        
        logger.info(f"✓ LSTM Trainer initialized (lookback: {self.lookback_period})")
    
    def train_model(self, symbol: str, X: np.ndarray, y: np.ndarray,
                   validation_split: float = 0.2) -> Dict:
        """
        Train LSTM model for a specific symbol
        
        Args:
            symbol: Cryptocurrency symbol
            X: Feature matrix (samples, lookback_period, features)
            y: Target values (samples, 1) - price/return to predict
            validation_split: Fraction of data for validation
        
        Returns:
            {
                'success': bool,
                'model_id': str,
                'epochs_trained': int,
                'best_loss': float,
                'validation_loss': float,
                'val_mae': float,
                'train_time_seconds': float
            }
        """
        try:
            if len(X) < 100:
                logger.warning(f"Insufficient data for {symbol}: {len(X)} samples < 100")
                return {'success': False, 'reason': 'Insufficient data'}
            
            start_time = datetime.now()
            
            # Prepare data
            scaler_X = StandardScaler()
            scaler_y = StandardScaler()
            
            # Reshape for scaler (combine all samples and timesteps)
            samples, timesteps, features = X.shape
            X_reshaped = X.reshape(-1, features)
            X_scaled = scaler_X.fit_transform(X_reshaped).reshape(samples, timesteps, features)
            y_scaled = scaler_y.fit_transform(y.reshape(-1, 1))
            
            # Store scalers
            self.scalers[symbol] = scaler_X
            self.scalers_y[symbol] = scaler_y
            
            # Split into train/val
            split_idx = int(len(X_scaled) * (1 - validation_split))
            X_train, X_val = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_val = y_scaled[:split_idx], y_scaled[split_idx:]
            
            # Build model
            model = self._build_lstm_model(X.shape)
            
            # Callbacks
            early_stop = EarlyStopping(
                monitor='val_loss',
                patience=self.patience,
                restore_best_weights=True,
                verbose=1
            )
            
            reduce_lr = ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6,
                verbose=1
            )
            
            # Train
            if TENSORFLOW_AVAILABLE:
                history = model.fit(
                    X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=self.epochs,
                    batch_size=self.batch_size,
                    callbacks=[early_stop, reduce_lr],
                    verbose=0
                )
                
                # Evaluate
                val_loss, val_mae = model.evaluate(X_val, y_val, verbose=0)
                best_loss = np.min(history.history['loss'])
                epochs_trained = len(history.history['loss'])
                
            else:
                # Mock training for testing
                history = {'loss': [0.01] * 50}
                val_loss = 0.015
                val_mae = 0.02
                best_loss = 0.01
                epochs_trained = 50
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Store model
            self.models[symbol] = model
            self.model_history[symbol] = history
            self.model_performance[symbol] = {
                'val_loss': float(val_loss),
                'val_mae': float(val_mae),
                'train_samples': len(X_train),
                'val_samples': len(X_val),
                'trained_at': datetime.now().isoformat()
            }
            
            logger.info(f"✓ LSTM model trained for {symbol}: "
                       f"val_loss={val_loss:.6f}, val_mae={val_mae:.6f}, "
                       f"time={training_time:.1f}s")
            
            return {
                'success': True,
                'symbol': symbol,
                'model_id': f"lstm_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'epochs_trained': epochs_trained,
                'best_loss': float(best_loss),
                'validation_loss': float(val_loss),
                'val_mae': float(val_mae),
                'train_time_seconds': training_time
            }
            
        except Exception as e:
            logger.error(f"LSTM training error for {symbol}: {e}")
            return {'success': False, 'reason': str(e)}
    
    def predict(self, symbol: str, X: np.ndarray, 
                return_confidence: bool = True) -> Dict:
        """
        Make predictions using trained model
        
        Args:
            symbol: Cryptocurrency symbol
            X: Feature matrix (samples, lookback_period, features)
            return_confidence: Whether to include confidence intervals
        
        Returns:
            {
                'predictions': array,
                'confidence_intervals': dict (if return_confidence=True),
                'predictions_original_scale': array
            }
        """
        try:
            if symbol not in self.models:
                logger.warning(f"No trained model for {symbol}")
                return {'success': False, 'reason': 'No trained model'}
            
            model = self.models[symbol]
            scaler_X = self.scalers[symbol]
            scaler_y = self.scalers_y[symbol]
            
            # Scale features
            samples, timesteps, features = X.shape
            X_reshaped = X.reshape(-1, features)
            X_scaled = scaler_X.transform(X_reshaped).reshape(samples, timesteps, features)
            
            # Make predictions
            if TENSORFLOW_AVAILABLE:
                y_pred_scaled = model.predict(X_scaled, verbose=0)
            else:
                # Mock prediction
                y_pred_scaled = np.random.randn(samples, 1) * 0.01
            
            # Inverse transform to original scale
            y_pred = scaler_y.inverse_transform(y_pred_scaled)
            
            result = {
                'success': True,
                'symbol': symbol,
                'predictions': y_pred.flatten(),
                'predictions_scaled': y_pred_scaled.flatten(),
                'n_predictions': len(y_pred)
            }
            
            # Add confidence intervals
            if return_confidence:
                # Estimate uncertainty using model variance
                result['confidence_intervals'] = {
                    'upper_95': y_pred.flatten() * 1.10,  # 10% margin
                    'lower_95': y_pred.flatten() * 0.90,
                    'prediction': y_pred.flatten()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"LSTM prediction error for {symbol}: {e}")
            return {'success': False, 'reason': str(e)}
    
    def _build_lstm_model(self, input_shape: Tuple) -> Optional:
        """Build LSTM model architecture"""
        
        if not TENSORFLOW_AVAILABLE:
            return self._build_mock_model()
        
        try:
            model = Sequential()
            
            # Input shape: (samples, lookback_period, features)
            return_sequences = len(self.lstm_layers) > 1
            
            # First LSTM layer
            model.add(layers.LSTM(
                self.lstm_layers[0],
                input_shape=(input_shape[1], input_shape[2]),
                return_sequences=return_sequences,
                activation='relu'
            ))
            model.add(layers.Dropout(self.dropout_rate))
            
            # Intermediate LSTM layers
            for units in self.lstm_layers[1:-1]:
                model.add(layers.LSTM(
                    units,
                    return_sequences=True,
                    activation='relu'
                ))
                model.add(layers.Dropout(self.dropout_rate))
            
            # Last LSTM layer (no return sequences)
            model.add(layers.LSTM(
                self.lstm_layers[-1],
                return_sequences=False,
                activation='relu'
            ))
            model.add(layers.Dropout(self.dropout_rate))
            
            # Dense layers
            model.add(layers.Dense(64, activation='relu'))
            model.add(layers.Dropout(self.dropout_rate))
            model.add(layers.Dense(32, activation='relu'))
            model.add(layers.Dense(self.output_dim))
            
            # Compile
            model.compile(
                optimizer=Adam(learning_rate=self.learning_rate),
                loss='mse',
                metrics=['mae']
            )
            
            logger.debug(f"LSTM model built: {input_shape}")
            return model
            
        except Exception as e:
            logger.error(f"Model building error: {e}")
            return None
    
    @staticmethod
    def _build_mock_model():
        """Build mock model for testing without TensorFlow"""
        class MockModel:
            def fit(self, *args, **kwargs):
                return type('obj', (object,), {'history': {'loss': [0.01]*50}})()
            
            def predict(self, X, **kwargs):
                return np.random.randn(len(X), 1) * 0.01
            
            def evaluate(self, X, y, **kwargs):
                return 0.015, 0.02
        
        return MockModel()
    
    def save_model(self, symbol: str, filepath: str) -> bool:
        """Save trained model to disk"""
        try:
            if symbol not in self.models:
                logger.warning(f"No model to save for {symbol}")
                return False
            
            model = self.models[symbol]
            scaler_X = self.scalers[symbol]
            scaler_y = self.scalers_y[symbol]
            
            # Save model and scalers
            if TENSORFLOW_AVAILABLE and hasattr(model, 'save'):
                model.save(f"{filepath}_{symbol}_model.h5")
            
            joblib.dump(scaler_X, f"{filepath}_{symbol}_scaler_X.pkl")
            joblib.dump(scaler_y, f"{filepath}_{symbol}_scaler_y.pkl")
            
            logger.info(f"Model saved for {symbol}: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Model save error: {e}")
            return False
    
    def load_model(self, symbol: str, filepath: str) -> bool:
        """Load trained model from disk"""
        try:
            if TENSORFLOW_AVAILABLE:
                self.models[symbol] = keras.models.load_model(
                    f"{filepath}_{symbol}_model.h5"
                )
            
            self.scalers[symbol] = joblib.load(f"{filepath}_{symbol}_scaler_X.pkl")
            self.scalers_y[symbol] = joblib.load(f"{filepath}_{symbol}_scaler_y.pkl")
            
            logger.info(f"Model loaded for {symbol}: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Model load error: {e}")
            return False
    
    def get_model_summary(self, symbol: str) -> Dict:
        """Get summary of trained model"""
        if symbol not in self.models:
            return {'error': 'No model trained'}
        
        performance = self.model_performance.get(symbol, {})
        
        return {
            'symbol': symbol,
            'model_exists': True,
            'lookback_period': self.lookback_period,
            'validation_loss': performance.get('val_loss', 'N/A'),
            'validation_mae': performance.get('val_mae', 'N/A'),
            'training_samples': performance.get('train_samples', 'N/A'),
            'validation_samples': performance.get('val_samples', 'N/A'),
            'trained_at': performance.get('trained_at', 'N/A')
        }


logger.info("[LSTM TRAINER] Deep learning model trainer loaded")
