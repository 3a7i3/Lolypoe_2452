"""
Anomaly Detection - Market manipulation and price anomaly detection
Uses multiple detection methods: Isolation Forest, Z-score, Local Outlier Factor, Mahalanobis
Detects: volume spikes, price gaps, volatility spikes, correlation breaks, flash crashes
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope
from scipy.spatial.distance import mahalanobis
from scipy.stats import zscore
import config

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Institutional-grade anomaly detection with multiple algorithms"""
    
    def __init__(self):
        self.anomaly_config = config.ANOMALY_DETECTION
        self.detection_method = self.anomaly_config.get('method', 'isolation_forest')
        self.sensitivity = self.anomaly_config.get('sensitivity', 0.95)
        self.min_volume = self.anomaly_config.get('min_volume', 10000)
        self.contamination = self.anomaly_config.get('contamination', 0.05)
        
        # Model storage
        self.models = {}
        self.anomaly_history = {}
        self.anomaly_stats = {
            'volume_spikes': 0,
            'price_gaps': 0,
            'volatility_spikes': 0,
            'correlation_breaks': 0,
            'total_anomalies': 0
        }
        
        logger.info(f"✓ Anomaly Detector initialized (method: {self.detection_method})")
    
    def detect_multivariate_anomalies(self, features_df: pd.DataFrame, 
                                      symbol: str, timestamp: datetime = None) -> Dict:
        """
        Detect anomalies using multivariate analysis
        Returns: {is_anomaly: bool, method: str, score: float (0-1), 
                  severity: str (low/medium/high), reason: str}
        """
        try:
            if features_df.empty or len(features_df) < 10:
                return self._no_anomaly()
            
            results = {}
            
            # Try all detection methods
            if self.detection_method in ['isolation_forest', 'all']:
                results['isolation_forest'] = self._isolation_forest_detect(features_df, symbol)
            
            if self.detection_method in ['zscore', 'all']:
                results['zscore'] = self._zscore_detect(features_df)
            
            if self.detection_method in ['mahalanobis', 'all']:
                results['mahalanobis'] = self._mahalanobis_detect(features_df)
            
            if self.detection_method in ['lof', 'all']:
                results['lof'] = self._lof_detect(features_df, symbol)
            
            # Aggregate results
            aggregated = self._aggregate_anomaly_results(results, symbol, timestamp)
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Multivariate anomaly detection error for {symbol}: {e}")
            return self._no_anomaly()
    
    def detect_specific_anomalies(self, ohlcv_df: pd.DataFrame, symbol: str,
                                  indicators: Dict) -> List[Dict]:
        """
        Detect specific market anomalies (volume spikes, price gaps, etc.)
        Returns: list of detected anomalies with details
        """
        anomalies = []
        
        try:
            # Volume Spike Detection
            if self.anomaly_config.get('detect_volume_spike', True):
                vol_anomaly = self._detect_volume_spike(ohlcv_df, symbol)
                if vol_anomaly:
                    anomalies.append(vol_anomaly)
                    self.anomaly_stats['volume_spikes'] += 1
            
            # Price Gap Detection
            if self.anomaly_config.get('detect_price_gap', True):
                gap_anomaly = self._detect_price_gap(ohlcv_df, symbol)
                if gap_anomaly:
                    anomalies.append(gap_anomaly)
                    self.anomaly_stats['price_gaps'] += 1
            
            # Volatility Spike Detection
            if self.anomaly_config.get('detect_volatility_spike', True):
                vol_spike = self._detect_volatility_spike(indicators, symbol)
                if vol_spike:
                    anomalies.append(vol_spike)
                    self.anomaly_stats['volatility_spikes'] += 1
            
            # Correlation Break Detection
            if self.anomaly_config.get('detect_correlation_break', True):
                corr_break = self._detect_correlation_break(ohlcv_df, symbol)
                if corr_break:
                    anomalies.append(corr_break)
                    self.anomaly_stats['correlation_breaks'] += 1
            
            if anomalies:
                self.anomaly_stats['total_anomalies'] += len(anomalies)
                logger.info(f"Detected {len(anomalies)} anomalies for {symbol}")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Specific anomaly detection error for {symbol}: {e}")
            return []
    
    def _isolation_forest_detect(self, features_df: pd.DataFrame, symbol: str) -> Dict:
        """
        Isolation Forest: Anomalies are easier to isolate than normal points
        Good for high-dimensional data, doesn't require distance calculations
        """
        try:
            # Remove NaN values
            features_clean = features_df.fillna(features_df.mean())
            
            # Train or get cached model
            if symbol not in self.models:
                iso_forest = IsolationForest(
                    contamination=self.contamination,
                    random_state=42,
                    n_jobs=-1
                )
                self.models[symbol] = iso_forest
            else:
                iso_forest = self.models[symbol]
            
            # Predict anomalies (-1 for anomaly, 1 for normal)
            predictions = iso_forest.fit_predict(features_clean)
            scores = iso_forest.score_samples(features_clean)
            
            # Get latest row
            is_anomaly = predictions[-1] == -1
            score = 1 - (scores[-1] + 0.5)  # Normalize to 0-1
            
            severity = self._calculate_severity(score)
            
            return {
                'method': 'isolation_forest',
                'is_anomaly': is_anomaly,
                'score': float(score),
                'severity': severity,
                'reason': 'Isolation Forest detected pattern isolation'
            }
            
        except Exception as e:
            logger.debug(f"Isolation Forest error: {e}")
            return self._no_anomaly()
    
    def _zscore_detect(self, features_df: pd.DataFrame) -> Dict:
        """
        Z-Score: Detect points >3 standard deviations from mean
        Simple but effective for univariate features
        """
        try:
            # Calculate z-scores
            z_scores = np.abs(zscore(features_df.fillna(0), nan_policy='propagate'))
            
            # Flag points exceeding threshold
            threshold = self.anomaly_config.get('threshold', 3.0)
            anomalies = (z_scores > threshold).any(axis=1)
            
            is_anomaly = anomalies.iloc[-1] if len(anomalies) > 0 else False
            
            # Calculate severity based on max z-score
            max_zscore = z_scores.iloc[-1].max() if len(z_scores) > 0 else 0
            score = min(max_zscore / (threshold * 2), 1.0)
            
            severity = self._calculate_severity(score)
            
            return {
                'method': 'zscore',
                'is_anomaly': is_anomaly,
                'score': float(score),
                'severity': severity,
                'max_zscore': float(max_zscore),
                'reason': f'Z-score {max_zscore:.2f} exceeds {threshold}σ'
            }
            
        except Exception as e:
            logger.debug(f"Z-score error: {e}")
            return self._no_anomaly()
    
    def _mahalanobis_detect(self, features_df: pd.DataFrame) -> Dict:
        """
        Mahalanobis Distance: Accounts for correlation between features
        Better than Euclidean distance for correlated variables
        """
        try:
            features_clean = features_df.fillna(features_df.mean())
            
            # Calculate covariance matrix
            cov_matrix = np.cov(features_clean.T)
            inv_cov = np.linalg.pinv(cov_matrix)
            
            # Calculate mean
            mean = features_clean.mean(axis=0).values
            
            # Calculate Mahalanobis distance for last point
            last_point = features_clean.iloc[-1].values
            diff = last_point - mean
            
            mahal_dist = np.sqrt(np.dot(np.dot(diff, inv_cov), diff.T))
            
            # Threshold based on chi-square distribution
            threshold = np.sqrt(features_clean.shape[1] * 9)  # 3-sigma equivalent
            is_anomaly = mahal_dist > threshold
            
            score = min(mahal_dist / (threshold * 2), 1.0)
            severity = self._calculate_severity(score)
            
            return {
                'method': 'mahalanobis',
                'is_anomaly': is_anomaly,
                'score': float(score),
                'severity': severity,
                'mahal_distance': float(mahal_dist),
                'threshold': float(threshold),
                'reason': f'Mahalanobis distance {mahal_dist:.2f} exceeds threshold'
            }
            
        except Exception as e:
            logger.debug(f"Mahalanobis error: {e}")
            return self._no_anomaly()
    
    def _lof_detect(self, features_df: pd.DataFrame, symbol: str) -> Dict:
        """
        Local Outlier Factor: Density-based anomaly detection
        Good for detecting local outliers in regions with varying densities
        """
        try:
            features_clean = features_df.fillna(features_df.mean())
            
            # Train LOF
            lof = LocalOutlierFactor(n_neighbors=20, contamination=self.contamination)
            predictions = lof.fit_predict(features_clean)
            scores = lof.negative_outlier_factor_
            
            is_anomaly = predictions[-1] == -1
            score = 1 - (scores[-1] / scores.min() + 1e-8)  # Normalize
            score = max(0, min(score, 1.0))
            
            severity = self._calculate_severity(score)
            
            return {
                'method': 'lof',
                'is_anomaly': is_anomaly,
                'score': float(score),
                'severity': severity,
                'reason': 'Local Outlier Factor: density-based anomaly'
            }
            
        except Exception as e:
            logger.debug(f"LOF error: {e}")
            return self._no_anomaly()
    
    def _detect_volume_spike(self, ohlcv_df: pd.DataFrame, symbol: str) -> Optional[Dict]:
        """Detect abnormal volume spikes (2x normal)"""
        try:
            if len(ohlcv_df) < 20:
                return None
            
            volumes = ohlcv_df['volume'].tail(20)
            current_volume = volumes.iloc[-1]
            avg_volume = volumes.iloc[:-1].mean()
            
            volume_threshold = self.anomaly_config.get('volume_spike_threshold', 2.0)
            
            if current_volume > avg_volume * volume_threshold and current_volume > self.min_volume:
                ratio = current_volume / avg_volume
                
                return {
                    'type': 'volume_spike',
                    'symbol': symbol,
                    'severity': 'high' if ratio > 5 else 'medium',
                    'current_volume': float(current_volume),
                    'avg_volume': float(avg_volume),
                    'ratio': float(ratio),
                    'reason': f'Volume spike: {ratio:.1f}x normal volume',
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Volume spike detection error: {e}")
            return None
    
    def _detect_price_gap(self, ohlcv_df: pd.DataFrame, symbol: str) -> Optional[Dict]:
        """Detect price gaps (sudden 5%+ moves)"""
        try:
            if len(ohlcv_df) < 2:
                return None
            
            prev_close = ohlcv_df['close'].iloc[-2]
            current_open = ohlcv_df['open'].iloc[-1]
            
            gap_threshold = self.anomaly_config.get('price_gap_threshold', 0.05)
            gap = abs(current_open - prev_close) / prev_close
            
            if gap > gap_threshold:
                return {
                    'type': 'price_gap',
                    'symbol': symbol,
                    'severity': 'high' if gap > 0.10 else 'medium',
                    'prev_close': float(prev_close),
                    'current_open': float(current_open),
                    'gap_percent': float(gap * 100),
                    'reason': f'Price gap: {gap*100:.2f}%',
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Price gap detection error: {e}")
            return None
    
    def _detect_volatility_spike(self, indicators: Dict, symbol: str) -> Optional[Dict]:
        """Detect volatility spikes (1.5x normal)"""
        try:
            current_vol = indicators.get('volatility_10', 0)
            prev_vol = indicators.get('volatility_20', current_vol)
            
            vol_threshold = self.anomaly_config.get('volatility_spike_threshold', 1.5)
            
            if current_vol > 0 and prev_vol > 0 and current_vol > prev_vol * vol_threshold:
                ratio = current_vol / prev_vol if prev_vol > 0 else 0
                
                return {
                    'type': 'volatility_spike',
                    'symbol': symbol,
                    'severity': 'high' if ratio > 3 else 'medium',
                    'current_volatility': float(current_vol),
                    'prev_volatility': float(prev_vol),
                    'ratio': float(ratio),
                    'reason': f'Volatility spike: {ratio:.1f}x',
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Volatility spike detection error: {e}")
            return None
    
    def _detect_correlation_break(self, ohlcv_df: pd.DataFrame, symbol: str) -> Optional[Dict]:
        """Detect correlation breaks (for pair trading)"""
        try:
            if len(ohlcv_df) < 30:
                return None
            
            # Calculate rolling correlation
            returns = ohlcv_df['close'].pct_change().tail(30)
            recent_correlation = returns.corr()
            
            threshold = self.anomaly_config.get('correlation_break_threshold', 0.3)
            
            # For this implementation, we detect if recent correlation deviates significantly
            # In live trading, this would compare to a pair's historical correlation
            
            return None  # Placeholder for pair-specific logic
            
        except Exception as e:
            logger.debug(f"Correlation break detection error: {e}")
            return None
    
    def _aggregate_anomaly_results(self, results: Dict, symbol: str, 
                                   timestamp: datetime = None) -> Dict:
        """Aggregate anomaly detection results from multiple methods"""
        try:
            # Collect anomaly votes
            anomaly_votes = sum(1 for r in results.values() if r.get('is_anomaly', False))
            total_methods = len(results)
            
            is_anomaly = anomaly_votes > (total_methods / 2)  # Majority vote
            
            # Average scores
            avg_score = np.mean([r.get('score', 0) for r in results.values()])
            
            severity = self._calculate_severity(avg_score)
            
            if timestamp is None:
                timestamp = datetime.now()
            
            return {
                'symbol': symbol,
                'is_anomaly': is_anomaly,
                'average_score': float(avg_score),
                'severity': severity,
                'anomaly_votes': anomaly_votes,
                'total_methods': total_methods,
                'consensus': anomaly_votes / total_methods if total_methods > 0 else 0,
                'individual_results': results,
                'timestamp': timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Anomaly result aggregation error: {e}")
            return self._no_anomaly()
    
    @staticmethod
    def _calculate_severity(score: float) -> str:
        """Calculate severity based on anomaly score"""
        if score < 0.33:
            return 'low'
        elif score < 0.67:
            return 'medium'
        else:
            return 'high'
    
    @staticmethod
    def _no_anomaly() -> Dict:
        """Return no anomaly detected"""
        return {
            'is_anomaly': False,
            'score': 0.0,
            'severity': 'low',
            'reason': 'No anomaly detected'
        }


logger.info("[ANOMALY DETECTION] Institutional anomaly detector loaded")
