"""
Regime Detection - Detect market regimes (Bull, Bear, Sideways)
"""

import logging
from typing import Dict, List
import numpy as np
import config

logger = logging.getLogger(__name__)

class RegimeDetector:
    """Detect market regimes"""
    
    REGIMES = ['BULL', 'BEAR', 'SIDEWAYS']
    
    def __init__(self):
        self.current_regime = 'SIDEWAYS'
        self.regime_history = []
        logger.info("✓ Regime Detector initialized")
    
    async def detect_regime(self, prices: List[float]) -> Dict:
        """
        Detect current market regime
        Returns: {regime: str, confidence: float}
        """
        try:
            if len(prices) < config.REGIME_WINDOW:
                return {'regime': 'SIDEWAYS', 'confidence': 0.5}
            
            recent_prices = prices[-config.REGIME_WINDOW:]
            
            # Calculate average return
            returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
                      for i in range(1, len(recent_prices))]
            avg_return = np.mean(returns)
            volatility = np.std(returns)
            
            # Determine regime based on returns and volatility
            if avg_return > 0.01 and volatility < 0.02:
                regime = 'BULL'
                confidence = min(avg_return / 0.02, 1.0)
            elif avg_return < -0.01 and volatility < 0.02:
                regime = 'BEAR'
                confidence = min(-avg_return / 0.02, 1.0)
            else:
                regime = 'SIDEWAYS'
                confidence = 0.7
            
            self.current_regime = regime
            self.regime_history.append({'regime': regime, 'confidence': confidence})
            
            logger.info(f"Regime: {regime} (confidence: {confidence:.2%})")
            
            return {
                'regime': regime,
                'confidence': confidence,
                'avg_return': avg_return,
                'volatility': volatility
            }
            
        except Exception as e:
            logger.error(f"Regime detection error: {e}")
            return {'regime': 'SIDEWAYS', 'confidence': 0.5}
    
    def get_regime_transitions(self) -> List:
        """Get regime transitions"""
        try:
            transitions = []
            
            for i in range(1, len(self.regime_history)):
                if self.regime_history[i]['regime'] != self.regime_history[i-1]['regime']:
                    transitions.append({
                        'from': self.regime_history[i-1]['regime'],
                        'to': self.regime_history[i]['regime'],
                        'index': i
                    })
            
            return transitions
            
        except Exception as e:
            logger.error(f"Regime transitions error: {e}")
            return []
