"""
Anomaly Detection - Detect market anomalies and outliers
"""

import logging
from typing import Dict, List
import numpy as np
from scipy.stats import zscore
import config

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Detect market anomalies"""
    
    def __init__(self):
        self.anomalies = []
        logger.info("✓ Anomaly Detector initialized")
    
    async def detect_anomalies(self, prices: List[float], volumes: List[float]) -> Dict:
        """
        Detect anomalies in price and volume
        Returns: detected anomalies
        """
        try:
            anomalies = {
                'price_anomalies': [],
                'volume_anomalies': []
            }
            
            # Detect price anomalies
            if len(prices) > 10:
                z_scores = zscore(prices[-20:])
                
                for i, z in enumerate(z_scores):
                    if abs(z) > config.ANOMALY_THRESHOLD:
                        anomalies['price_anomalies'].append({
                            'index': len(prices) - 20 + i,
                            'price': prices[-(20-i)],
                            'z_score': z,
                            'severity': min(abs(z) / config.ANOMALY_THRESHOLD, 2.0)
                        })
            
            # Detect volume anomalies
            if len(volumes) > 10:
                avg_volume = np.mean(volumes[-20:])
                
                for i, vol in enumerate(volumes[-20:]):
                    if vol > avg_volume * 2:
                        anomalies['volume_anomalies'].append({
                            'index': len(volumes) - 20 + i,
                            'volume': vol,
                            'avg_volume': avg_volume,
                            'ratio': vol / avg_volume
                        })
            
            if anomalies['price_anomalies'] or anomalies['volume_anomalies']:
                logger.info(f"Detected {len(anomalies['price_anomalies'])} price anomalies "
                           f"and {len(anomalies['volume_anomalies'])} volume anomalies")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return {'price_anomalies': [], 'volume_anomalies': []}
    
    def is_anomalous(self, price: float, volume: float, 
                     avg_price: float, avg_volume: float) -> bool:
        """
        Check if a single price/volume is anomalous
        Returns: True if anomalous
        """
        try:
            price_z_score = abs((price - avg_price) / (0.001 + abs(avg_price)))
            volume_ratio = volume / (0.001 + avg_volume)
            
            return (price_z_score > config.ANOMALY_THRESHOLD or 
                   volume_ratio > 3.0)  # Volume 3x average
            
        except Exception as e:
            logger.debug(f"Anomaly check error: {e}")
            return False
