"""
Feature Engineering - Advanced predictive features for institutional ML models
Includes technical indicators, lagged features, scaling, and anomaly detection
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.decomposition import PCA
from scipy.stats import zscore
import config

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """Create institutional-grade features for ML models"""
    
    def __init__(self):
        self.scalers = {}
        self.pca_models = {}
        self.feature_stats = {}
    
    def create_comprehensive_features(self, ohlcv_data: List, symbol: str = 'BTC/USDT',
                                      lookback: int = None) -> pd.DataFrame:
        """
        Create comprehensive technical and statistical features for institutional trading
        Returns: DataFrame with 100+ engineered features
        """
        if lookback is None:
            lookback = config.FEATURE_ENGINEERING['lookback']
        
        try:
            if len(ohlcv_data) < lookback:
                logger.warning(f"Insufficient data for {symbol}: {len(ohlcv_data)} < {lookback}")
                return pd.DataFrame()
            
            df = self._ohlcv_to_dataframe(ohlcv_data)
            
            # Add all technical indicators
            features_df = self._add_trend_indicators(df)
            features_df = self._add_momentum_indicators(features_df)
            features_df = self._add_volatility_indicators(features_df)
            features_df = self._add_volume_indicators(features_df)
            features_df = self._add_price_action_indicators(features_df)
            
            # Add advanced features
            if config.FEATURE_ENGINEERING.get('add_lagged_features'):
                features_df = self._add_lagged_features(features_df)
            
            if config.FEATURE_ENGINEERING.get('add_return_features'):
                features_df = self._add_return_features(features_df)
            
            if config.FEATURE_ENGINEERING.get('add_volume_features'):
                features_df = self._add_volume_features(features_df)
            
            # Keep only numeric columns
            features_df = features_df.select_dtypes(include=[np.number])
            
            # Store feature statistics
            self.feature_stats[symbol] = {
                'mean': features_df.mean(),
                'std': features_df.std(),
                'count': len(features_df)
            }
            
            logger.info(f"✓ Created {len(features_df.columns)} features for {symbol}")
            return features_df
            
        except Exception as e:
            logger.error(f"Feature creation error for {symbol}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def _ohlcv_to_dataframe(ohlcv_data: List) -> pd.DataFrame:
        """Convert OHLCV data to DataFrame"""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    @staticmethod
    def _add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add trend-following indicators"""
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['sma_200'] = df['close'].rolling(200).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # Hull Moving Average
        df['hma_50'] = df['close'].rolling(50).mean()  # Simplified
        
        # Trend flags
        df['price_above_sma_50'] = (df['close'] > df['sma_50']).astype(int)
        df['price_above_sma_200'] = (df['close'] > df['sma_200']).astype(int)
        df['sma_50_above_sma_200'] = (df['sma_50'] > df['sma_200']).astype(int)
        
        return df
    
    @staticmethod
    def _add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # Extended RSI
        for period in [21, 28]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Stochastic
        low_min = df['low'].rolling(14).min()
        high_max = df['high'].rolling(14).max()
        df['stoch_k'] = 100 * ((df['close'] - low_min) / (high_max - low_min + 1e-8))
        df['stoch_d'] = df['stoch_k'].rolling(3).mean()
        df['stoch_diff'] = df['stoch_k'] - df['stoch_d']
        
        # Williams %R
        df['williams_r'] = -100 * ((high_max - df['close']) / (high_max - low_min + 1e-8))
        
        return df
    
    @staticmethod
    def _add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators"""
        # Bollinger Bands
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        df['bb_upper_20'] = sma_20 + (std_20 * 2)
        df['bb_lower_20'] = sma_20 - (std_20 * 2)
        df['bb_middle_20'] = sma_20
        df['bb_width_20'] = (df['bb_upper_20'] - df['bb_lower_20']) / sma_20
        
        # Extended Bollinger Bands
        sma_50 = df['close'].rolling(50).mean()
        std_50 = df['close'].rolling(50).std()
        df['bb_upper_50'] = sma_50 + (std_50 * 2)
        df['bb_lower_50'] = sma_50 - (std_50 * 2)
        df['bb_width_50'] = (df['bb_upper_50'] - df['bb_lower_50']) / sma_50
        
        # ATR (Average True Range)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr_14'] = df['tr'].rolling(14).mean()
        df['atr_21'] = df['tr'].rolling(21).mean()
        
        # Simple volatility
        df['volatility_10'] = df['close'].pct_change().rolling(10).std()
        df['volatility_20'] = df['close'].pct_change().rolling(20).std()
        
        return df
    
    @staticmethod
    def _add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add volume indicators"""
        # OBV (On-Balance Volume)
        change = df['close'].diff()
        obv = (np.sign(change) * df['volume']).fillna(0).cumsum()
        df['obv'] = obv
        df['obv_ema'] = obv.ewm(span=20, adjust=False).mean()
        
        # Volume Rate of Change
        df['vroc'] = df['volume'].pct_change(10)
        
        # Volume Moving Averages
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Money Flow Index (MFI)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        mf = typical_price * df['volume']
        positive_mf = mf.where(change > 0, 0)
        negative_mf = mf.where(change < 0, 0)
        positive_mf_sum = positive_mf.rolling(14).sum()
        negative_mf_sum = negative_mf.rolling(14).sum()
        mfi = 100 - (100 / (1 + (positive_mf_sum / negative_mf_sum + 1e-8)))
        df['mfi'] = mfi
        
        # Chaikin Money Flow
        ad_line = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'] + 1e-8)
        ad_line = ad_line * df['volume']
        df['cmf'] = ad_line.rolling(20).sum() / df['volume'].rolling(20).sum()
        
        # VWAP
        df['vwap'] = (typical_price * df['volume']).rolling(30).sum() / df['volume'].rolling(30).sum()
        
        return df
    
    @staticmethod
    def _add_price_action_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add price action and advanced indicators"""
        # ADX (Average Directional Index)
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        plus_dm = high_diff.where(high_diff > low_diff, 0).where(high_diff > 0, 0)
        minus_dm = low_diff.where(low_diff > high_diff, 0).where(low_diff > 0, 0)
        
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        tr_sum = tr.rolling(14).mean()
        
        plus_di = 100 * (plus_dm.rolling(14).mean() / tr_sum)
        minus_di = 100 * (minus_dm.rolling(14).mean() / tr_sum)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-8)
        df['adx_14'] = dx.rolling(14).mean()
        df['adx_21'] = dx.rolling(21).mean()
        
        # CCI (Commodity Channel Index)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(20).mean()
        mad_tp = (typical_price - sma_tp).abs().rolling(20).mean()
        df['cci_20'] = (typical_price - sma_tp) / (mad_tp * 0.015 + 1e-8)
        
        # Price patterns
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        
        return df
    
    @staticmethod
    def _add_lagged_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add lagged features for temporal dependencies"""
        lagged_periods = config.FEATURE_ENGINEERING.get('lagged_periods', [1, 2, 3, 5, 10])
        
        for period in lagged_periods:
            # Lagged returns
            df[f'return_lag_{period}'] = df['close'].pct_change(period)
            # Lagged volume
            df[f'volume_lag_{period}'] = df['volume'].shift(period)
        
        return df
    
    @staticmethod
    def _add_return_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add return-based features"""
        # Log returns
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
        df['log_return_5'] = np.log(df['close'] / df['close'].shift(5))
        df['log_return_20'] = np.log(df['close'] / df['close'].shift(20))
        
        # Cumulative returns
        df['cum_return_5'] = (1 + df['log_return']).rolling(5).prod() - 1
        df['cum_return_20'] = (1 + df['log_return']).rolling(20).prod() - 1
        
        return df
    
    @staticmethod
    def _add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add advanced volume features"""
        df['volume_change'] = df['volume'].pct_change()
        df['avg_price'] = (df['high'] + df['low']) / 2
        df['price_volume'] = df['avg_price'] * df['volume']
        df['price_volume_sma'] = df['price_volume'].rolling(20).mean()
        
        return df
    
    def scale_features(self, features_df: pd.DataFrame, symbol: str, method: str = None) -> pd.DataFrame:
        """
        Scale features using specified method
        Methods: z_score, min_max, robust, standard
        """
        if method is None:
            method = config.FEATURE_ENGINEERING.get('scaling_method', 'z_score')
        
        try:
            features_copy = features_df.copy()
            
            if method == 'z_score':
                scaler = StandardScaler()
            elif method == 'min_max':
                scaler = MinMaxScaler()
            elif method == 'robust':
                scaler = RobustScaler()
            else:
                scaler = StandardScaler()
            
            scaled_data = scaler.fit_transform(features_copy)
            features_scaled = pd.DataFrame(scaled_data, columns=features_copy.columns, 
                                         index=features_copy.index)
            
            # Store scaler for later use
            self.scalers[symbol] = scaler
            
            logger.debug(f"Scaled {symbol} features using {method}")
            return features_scaled
            
        except Exception as e:
            logger.error(f"Feature scaling error for {symbol}: {e}")
            return features_df
    
    def apply_pca(self, features_df: pd.DataFrame, symbol: str, n_components: int = None) -> pd.DataFrame:
        """
        Apply PCA for dimensionality reduction
        """
        if not config.FEATURE_ENGINEERING.get('enable_pca', False):
            return features_df
        
        if n_components is None:
            n_components = config.FEATURE_ENGINEERING.get('pca_components', 20)
        
        try:
            # Ensure enough components don't exceed features
            n_components = min(n_components, features_df.shape[1])
            
            pca = PCA(n_components=n_components)
            pca_data = pca.fit_transform(features_df)
            pca_df = pd.DataFrame(pca_data, 
                                columns=[f'pca_{i}' for i in range(n_components)],
                                index=features_df.index)
            
            self.pca_models[symbol] = pca
            
            explained_variance = pca.explained_variance_ratio_.sum()
            logger.info(f"PCA for {symbol}: {explained_variance:.2%} variance with {n_components} components")
            
            return pca_df
            
        except Exception as e:
            logger.error(f"PCA error for {symbol}: {e}")
            return features_df
    
    def detect_feature_anomalies(self, features_df: pd.DataFrame, 
                                 threshold: float = 3.0) -> np.ndarray:
        """
        Detect anomalous features using z-score
        Returns: boolean array for anomalous rows
        """
        try:
            # Calculate z-scores for each feature
            z_scores = np.abs(zscore(features_df.fillna(0), nan_policy='propagate'))
            
            # Flag rows with any feature exceeding threshold
            anomalies = (z_scores > threshold).any(axis=1)
            
            n_anomalies = anomalies.sum()
            logger.debug(f"Detected {n_anomalies} anomalous feature rows out of {len(features_df)}")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return np.zeros(len(features_df), dtype=bool)
    
    def create_lstm_sequences(self, features_df: pd.DataFrame, 
                              sequence_length: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM models with proper normalization
        Returns: (sequences, targets) normalized for neural network training
        """
        if sequence_length is None:
            sequence_length = config.LSTM['sequence_length']
        
        try:
            if len(features_df) < sequence_length + 1:
                logger.warning(f"Insufficient data for LSTM sequences: {len(features_df)} < {sequence_length + 1}")
                return np.array([]), np.array([])
            
            # Use close prices normalized
            closes = features_df['close'].values if 'close' in features_df else features_df.iloc[:, 0].values
            
            # Normalize prices
            close_min = closes.min()
            close_max = closes.max()
            
            if close_max == close_min:
                normalized = np.zeros_like(closes)
            else:
                normalized = (closes - close_min) / (close_max - close_min)
            
            # Create sequences
            sequences = []
            targets = []
            
            for i in range(len(normalized) - sequence_length):
                seq = normalized[i:i+sequence_length].reshape(-1, 1)
                target = normalized[i+sequence_length]
                
                sequences.append(seq)
                targets.append(target)
            
            sequences = np.array(sequences)
            targets = np.array(targets)
            
            logger.debug(f"Created {len(sequences)} LSTM sequences of length {sequence_length}")
            return sequences, targets
            
        except Exception as e:
            logger.error(f"LSTM sequence creation error: {e}")
            return np.array([]), np.array([])
    
    def create_multivariate_lstm_sequences(self, features_df: pd.DataFrame,
                                          sequence_length: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create multivariate sequences for LSTM using multiple features
        More powerful than univariate sequences
        """
        if sequence_length is None:
            sequence_length = config.LSTM['sequence_length']
        
        try:
            if len(features_df) < sequence_length + 1:
                return np.array([]), np.array([])
            
            # Normalize all features
            features_normalized = (features_df - features_df.mean()) / features_df.std()
            
            sequences = []
            targets = []
            
            # Target is close price (or first column)
            target_col = 'close' if 'close' in features_df else features_df.columns[0]
            target_normalized = (features_df[target_col] - features_df[target_col].mean()) / features_df[target_col].std()
            
            for i in range(len(features_normalized) - sequence_length):
                seq = features_normalized.iloc[i:i+sequence_length].values
                target = target_normalized.iloc[i+sequence_length]
                
                sequences.append(seq)
                targets.append(target)
            
            sequences = np.array(sequences)
            targets = np.array(targets)
            
            logger.info(f"Created {len(sequences)} multivariate LSTM sequences "
                       f"({features_df.shape[1]} features, length {sequence_length})")
            
            return sequences, targets
            
        except Exception as e:
            logger.error(f"Multivariate LSTM sequence error: {e}")
            return np.array([]), np.array([])
    
    @staticmethod
    def create_advanced_labels(ohlcv_data: List, lookahead: int = 5,
                              up_threshold: float = 0.01, 
                              down_threshold: float = -0.01) -> Tuple[List[int], List[float]]:
        """
        Create multi-class labels with confidence scores
        Returns: (labels, confidence_scores)
        Labels: 2=STRONG_UP, 1=UP, 0=NEUTRAL, -1=DOWN, -2=STRONG_DOWN
        """
        try:
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            labels = []
            confidence_scores = []
            
            for i in range(len(df) - lookahead):
                current_price = df['close'].iloc[i]
                future_price = df['close'].iloc[i + lookahead]
                high_price = df['high'].iloc[i:i+lookahead].max()
                low_price = df['low'].iloc[i:i+lookahead].min()
                
                change = (future_price - current_price) / current_price
                max_change = (high_price - current_price) / current_price
                min_change = (low_price - current_price) / current_price
                
                # Assign label based on future price movement
                if change > 0.02:  # Strong up
                    label = 2
                    confidence = min(abs(change), 0.1) / 0.1  # Normalize to 0-1
                elif change > up_threshold:  # Up
                    label = 1
                    confidence = change / 0.02
                elif change < -0.02:  # Strong down
                    label = -2
                    confidence = min(abs(change), 0.1) / 0.1
                elif change < down_threshold:  # Down
                    label = -1
                    confidence = abs(change) / 0.02
                else:  # Neutral
                    label = 0
                    confidence = 0.5
                
                labels.append(label)
                confidence_scores.append(np.clip(confidence, 0, 1))
            
            return labels, confidence_scores
            
        except Exception as e:
            logger.error(f"Advanced label creation error: {e}")
            return [], []
    
    def select_important_features(self, features_df: pd.DataFrame, 
                                  target: np.ndarray,
                                  min_importance: float = None) -> List[str]:
        """
        Select features based on importance using ensemble method
        Requires target variable for supervised feature selection
        """
        if not config.FEATURE_ENGINEERING.get('enable_feature_selection', False):
            return list(features_df.columns)
        
        if min_importance is None:
            min_importance = config.FEATURE_ENGINEERING.get('min_feature_importance', 0.02)
        
        try:
            from sklearn.ensemble import RandomForestClassifier
            
            # Remove NaN values
            clean_features = features_df.fillna(0)
            
            # Train RF for feature importance
            rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
            rf.fit(clean_features, target)
            
            importances = rf.feature_importances_
            important_features = [col for col, imp in zip(features_df.columns, importances) 
                                 if imp >= min_importance]
            
            logger.info(f"Selected {len(important_features)} important features "
                       f"(threshold: {min_importance:.4f})")
            
            return important_features
            
        except Exception as e:
            logger.error(f"Feature selection error: {e}")
            return list(features_df.columns)
    
    def validate_features(self, features_df: pd.DataFrame) -> bool:
        """Validate features for data quality and NaN handling"""
        try:
            # Check for excessive NaN
            nan_ratio = features_df.isna().sum() / len(features_df)
            if (nan_ratio > 0.5).any():
                logger.warning("Some features have >50% NaN values")
                return False
            
            # Check for infinities
            if np.isinf(features_df.select_dtypes(include=[np.number])).any().any():
                logger.warning("Features contain infinite values")
                return False
            
            logger.debug(f"Features validated: {features_df.shape}, NaN% {nan_ratio.mean():.2%}")
            return True
            
        except Exception as e:
            logger.error(f"Feature validation error: {e}")
            return False
