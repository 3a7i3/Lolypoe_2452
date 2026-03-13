"""
Regime Detection - Detection de regimes de marche
"""

import numpy as np
from config import REGIME_WINDOW, REGIME_THRESHOLD
from utils.logger import logger

class RegimeDetector:
    """Detecte les regimes de marche."""
    
    REGIMES = ['BULL', 'BEAR', 'SIDEWAYS']
    
    @staticmethod
    def detect_regime(data):
        """Detecte le regime actuel."""
        if len(data) < REGIME_WINDOW:
            return 'UNKNOWN'
        
        try:
            # Analyser les N derniers jours
            recent = data.iloc[-REGIME_WINDOW:].copy()
            
            # Calculer returns
            returns = recent['Close'].pct_change().dropna()
            mean_return = returns.mean()
            std_return = returns.std()
            
            # Calculer SMA pour la tendance
            sma_short = recent['Close'].rolling(10).mean().iloc[-1]
            sma_long = recent['Close'].rolling(50).mean().iloc[-1]
            
            current_price = recent['Close'].iloc[-1]
            
            # Detection du regime
            if mean_return > std_return * REGIME_THRESHOLD and current_price > sma_short > sma_long:
                return 'BULL'
            elif mean_return < -std_return * REGIME_THRESHOLD and current_price < sma_short < sma_long:
                return 'BEAR'
            else:
                return 'SIDEWAYS'
        
        except Exception as e:
            logger.error(f"Erreur detection regime: {e}")
            return 'UNKNOWN'
    
    @staticmethod
    def get_regime_confidence(data):
        """Retourne la confiance du regime."""
        if len(data) < REGIME_WINDOW:
            return 0.0
        
        try:
            recent = data.iloc[-REGIME_WINDOW:].copy()
            returns = recent['Close'].pct_change().dropna()
            
            # Compter les periodes haussières/baissieres
            bull_days = len(returns[returns > 0])
            bear_days = len(returns[returns < 0])
            total_days = len(returns)
            
            confidence = max(bull_days, bear_days) / total_days if total_days > 0 else 0.5
            return confidence
        
        except:
            return 0.5
