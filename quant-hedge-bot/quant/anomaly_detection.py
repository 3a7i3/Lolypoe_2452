"""
Anomaly Detection - Detection des anomalies
"""

import numpy as np
from config import ANOMALY_THRESHOLD, ANOMALY_WINDOW
from utils.logger import logger

class AnomalyDetector:
    """Detecte les anomalies dans les donnees."""
    
    @staticmethod
    def detect_anomalies(data):
        """Detecte les anomalies."""
        if len(data) < ANOMALY_WINDOW:
            return []
        
        anomalies = []
        
        try:
            # Analyser returns
            returns = data['Close'].pct_change()
            mean_return = returns.rolling(ANOMALY_WINDOW).mean()
            std_return = returns.rolling(ANOMALY_WINDOW).std()
            
            # Identifier anomalies (z-score)
            z_scores = (returns - mean_return) / std_return
            
            for i, (date, z_score) in enumerate(z_scores.iloc[-ANOMALY_WINDOW:].items()):
                if abs(z_score) > ANOMALY_THRESHOLD:
                    anomalies.append({
                        'date': date,
                        'type': 'SPIKE' if z_score > 0 else 'DROP',
                        'severity': abs(z_score),
                        'price': data['Close'].iloc[-(ANOMALY_WINDOW-i)],
                        'return': returns.iloc[-(ANOMALY_WINDOW-i)]
                    })
            
            if anomalies:
                logger.warning(f"Anomalies detectees: {len(anomalies)}")
            
            return anomalies
        
        except Exception as e:
            logger.error(f"Erreur detection anomalies: {e}")
            return []
    
    @staticmethod
    def detect_volume_anomaly(data):
        """Detecte les anomalies de volume."""
        if len(data) < 20:
            return False
        
        try:
            recent_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].iloc[-20:-1].mean()
            
            # Si volume > 2x la moyenne
            if recent_volume > avg_volume * 2:
                logger.warning(f"Volume anomaly: {recent_volume:.0f} vs avg {avg_volume:.0f}")
                return True
            
            return False
        
        except:
            return False
