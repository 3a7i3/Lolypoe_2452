"""
Regime Detection - Market regime classification using Hidden Markov Models
Classifies market into: STRONG_BULL, BULL, NEUTRAL, BEAR, STRONG_BEAR
Uses HMM with returns, volatility, and trend features
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import norm
import config

logger = logging.getLogger(__name__)

class RegimeDetector:
    """Hidden Markov Model based market regime detection"""
    
    # Market regimes
    REGIMES = ['STRONG_BULL', 'BULL', 'NEUTRAL', 'BEAR', 'STRONG_BEAR']
    
    # Regime colors for visualization
    REGIME_COLORS = {
        'STRONG_BULL': '#00ff00',  # Green
        'BULL': '#90ee90',          # Light green
        'NEUTRAL': '#ffff00',       # Yellow
        'BEAR': '#ff6b6b',          # Red
        'STRONG_BEAR': '#8b0000'    # Dark red
    }
    
    def __init__(self):
        self.regime_config = config.REGIME_DETECTION
        self.n_regimes = self.regime_config.get('n_regimes', 5)
        self.lookback_period = self.regime_config.get('lookback_period', 30)
        self.confidence_threshold = self.regime_config.get('confidence_threshold', 0.70)
        
        # HMM parameters
        self.transition_matrix = None
        self.emission_params = {}
        self.initial_state_probs = np.array([1.0/self.n_regimes] * self.n_regimes)
        
        # State tracking
        self.current_regime = 'NEUTRAL'
        self.regime_history = {}
        self.confidence_scores = {}
        self.regime_switches = 0
        
        self._initialize_hmm()
        logger.info(f"✓ Regime Detector initialized ({self.n_regimes} regimes)")
    
    def _initialize_hmm(self):
        """Initialize Hidden Markov Model parameters"""
        
        # Transition matrix: probability of moving from regime i to regime j
        # Higher diagonal values = tendency to stay in same regime
        self.transition_matrix = np.array([
            [0.70, 0.20, 0.05, 0.03, 0.02],  # STRONG_BULL
            [0.15, 0.65, 0.15, 0.04, 0.01],  # BULL
            [0.05, 0.20, 0.50, 0.20, 0.05],  # NEUTRAL
            [0.01, 0.04, 0.15, 0.65, 0.15],  # BEAR
            [0.02, 0.03, 0.05, 0.20, 0.70]   # STRONG_BEAR
        ])
        
        # Emission parameters (mean and std for each feature given regime)
        self.emission_params = {
            'returns': {
                'STRONG_BULL': {'mean': 0.025, 'std': 0.015},
                'BULL': {'mean': 0.012, 'std': 0.010},
                'NEUTRAL': {'mean': 0.001, 'std': 0.008},
                'BEAR': {'mean': -0.012, 'std': 0.010},
                'STRONG_BEAR': {'mean': -0.025, 'std': 0.020}
            },
            'volatility': {
                'STRONG_BULL': {'mean': 0.012, 'std': 0.005},
                'BULL': {'mean': 0.015, 'std': 0.006},
                'NEUTRAL': {'mean': 0.020, 'std': 0.008},
                'BEAR': {'mean': 0.025, 'std': 0.010},
                'STRONG_BEAR': {'mean': 0.035, 'std': 0.012}
            },
            'trend': {
                'STRONG_BULL': {'mean': 0.8, 'std': 0.1},
                'BULL': {'mean': 0.6, 'std': 0.15},
                'NEUTRAL': {'mean': 0.5, 'std': 0.1},
                'BEAR': {'mean': 0.4, 'std': 0.15},
                'STRONG_BEAR': {'mean': 0.2, 'std': 0.1}
            }
        }
    
    def detect_regime(self, ohlcv_df: pd.DataFrame, indicators: Dict) -> Dict:
        """
        Detect current market regime using HMM
        
        Returns: {
            regime: str,
            confidence: float (0-1),
            probability_all: dict,
            regime_features: dict,
            switch_detected: bool,
            signal_strength: float (-1 to 1)
        }
        """
        try:
            if len(ohlcv_df) < self.lookback_period:
                return self._default_regime()
            
            # Extract features
            features = self._extract_regime_features(ohlcv_df, indicators)
            
            # Calculate emission probabilities
            emission_probs = self._calculate_emission_probabilities(features)
            
            # Run Viterbi algorithm for most likely state sequence
            viterbi_path, viterbi_probs = self._viterbi_algorithm(emission_probs)
            
            # Get current regime and confidence
            current_regime_idx = viterbi_path[-1]
            current_regime = self.REGIMES[current_regime_idx]
            confidence = viterbi_probs[-1, current_regime_idx]
            
            # Detect regime switches
            prev_regime = self.current_regime
            switch_detected = current_regime != prev_regime
            
            if switch_detected:
                self.regime_switches += 1
                logger.info(f"Regime switch: {prev_regime} → {current_regime} (confidence: {confidence:.2%})")
            
            # Calculate signal strength
            signal_strength = self._calculate_signal_strength(current_regime_idx)
            
            self.current_regime = current_regime
            
            # Store history
            timestamp = datetime.now().isoformat()
            self.regime_history[timestamp] = current_regime
            self.confidence_scores[timestamp] = confidence
            
            return {
                'regime': current_regime,
                'regime_index': current_regime_idx,
                'confidence': float(confidence),
                'probability_all': self._format_probabilities(viterbi_probs[-1]),
                'regime_color': self.REGIME_COLORS[current_regime],
                'regime_features': features,
                'switch_detected': switch_detected,
                'previous_regime': prev_regime,
                'signal_strength': float(signal_strength),
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Regime detection error: {e}")
            return self._default_regime()
    
    def _extract_regime_features(self, ohlcv_df: pd.DataFrame, 
                                 indicators: Dict) -> Dict:
        """Extract features for regime classification"""
        
        # 1. Returns feature
        returns = ohlcv_df['close'].pct_change().tail(self.lookback_period)
        avg_return = returns.mean()
        
        # 2. Volatility feature
        volatility = returns.std()
        
        # 3. Trend feature (0-1 scale)
        # Based on SMA positioning and price position relative to bands
        sma_short = ohlcv_df['close'].tail(self.lookback_period).mean()
        sma_long = ohlcv_df['close'].tail(60).mean() if len(ohlcv_df) >= 60 else sma_short
        
        recent_close = ohlcv_df['close'].iloc[-1]
        
        # Calculate trend score
        if sma_long != 0:
            trend_score = (recent_close - ohlcv_df['close'].min()) / (ohlcv_df['close'].max() - ohlcv_df['close'].min() + 1e-8)
        else:
            trend_score = 0.5
        
        trend_score = max(0, min(trend_score, 1.0))
        
        # 4. RSI from indicators
        rsi = indicators.get('rsi_14', 50) / 100.0  # Normalize to 0-1
        
        # 5. Volume trend
        volume_trend = indicators.get('volume_trend', 0) / 100  # Normalize
        
        # 6. Bollinger Bands position
        bb_position = indicators.get('bb_position', 0.5)
        
        return {
            'avg_return': float(avg_return),
            'volatility': float(volatility),
            'trend_score': float(trend_score),
            'rsi_normalized': float(rsi),
            'volume_trend': float(volume_trend),
            'bb_position': float(bb_position)
        }
    
    def _calculate_emission_probabilities(self, features: Dict) -> np.ndarray:
        """Calculate emission probability for each regime"""
        
        emission_probs = np.zeros((1, self.n_regimes))
        
        # Get feature values
        returns = features['avg_return']
        volatility = features['volatility']
        trend = features['trend_score']
        
        for i, regime in enumerate(self.REGIMES):
            # Probability based on returns
            return_prob = norm.pdf(
                returns,
                self.emission_params['returns'][regime]['mean'],
                self.emission_params['returns'][regime]['std']
            )
            
            # Probability based on volatility
            vol_prob = norm.pdf(
                volatility,
                self.emission_params['volatility'][regime]['mean'],
                self.emission_params['volatility'][regime]['std']
            )
            
            # Probability based on trend
            trend_prob = norm.pdf(
                trend,
                self.emission_params['trend'][regime]['mean'],
                self.emission_params['trend'][regime]['std']
            )
            
            # Combine probabilities (equal weighting)
            combined_prob = (return_prob * vol_prob * trend_prob) ** (1/3)
            emission_probs[0, i] = combined_prob
        
        # Normalize
        if emission_probs.sum() > 0:
            emission_probs = emission_probs / emission_probs.sum()
        else:
            emission_probs = np.ones((1, self.n_regimes)) / self.n_regimes
        
        return emission_probs
    
    def _viterbi_algorithm(self, emission_probs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Viterbi algorithm for finding most likely state sequence
        Returns: (viterbi_path, viterbi_probs)
        """
        T = emission_probs.shape[0]
        N = self.n_regimes
        
        # Initialize
        viterbi_probs = np.zeros((T, N))
        viterbi_path = np.zeros((T, N), dtype=int)
        
        # Forward pass
        viterbi_probs[0] = self.initial_state_probs * emission_probs[0]
        
        for t in range(1, T):
            for j in range(N):
                trans_probs = viterbi_probs[t-1] * self.transition_matrix[:, j]
                viterbi_path[t, j] = np.argmax(trans_probs)
                viterbi_probs[t, j] = np.max(trans_probs) * emission_probs[t, j]
        
        # Backtrack to find full path
        path = np.zeros(T, dtype=int)
        path[-1] = np.argmax(viterbi_probs[-1])
        
        for t in range(T-2, -1, -1):
            path[t] = viterbi_path[t+1, path[t+1]]
        
        return path, viterbi_probs
    
    def _calculate_signal_strength(self, regime_idx: int) -> float:
        """Calculate signal strength from regime (-1 to 1)"""
        if regime_idx == 0:      # STRONG_BULL
            return 1.0
        elif regime_idx == 1:    # BULL
            return 0.5
        elif regime_idx == 2:    # NEUTRAL
            return 0.0
        elif regime_idx == 3:    # BEAR
            return -0.5
        else:  # STRONG_BEAR (4)
            return -1.0
    
    def _format_probabilities(self, probs: np.ndarray) -> Dict[str, float]:
        """Format regime probabilities as dictionary"""
        return {
            regime: float(prob)
            for regime, prob in zip(self.REGIMES, probs)
        }
    
    @staticmethod
    def _default_regime() -> Dict:
        """Return default regime when insufficient data"""
        return {
            'regime': 'NEUTRAL',
            'regime_index': 2,
            'confidence': 0.5,
            'probability_all': {r: 0.2 for r in RegimeDetector.REGIMES},
            'regime_color': RegimeDetector.REGIME_COLORS['NEUTRAL'],
            'regime_features': {},
            'switch_detected': False,
            'signal_strength': 0.0,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_regime_history(self, last_n: int = 100) -> Dict:
        """Get regime history"""
        history = dict(sorted(self.regime_history.items())[-last_n:])
        return history
    
    def get_statistics(self) -> Dict:
        """Get regime detection statistics"""
        return {
            'current_regime': self.current_regime,
            'total_switches': self.regime_switches,
            'history_size': len(self.regime_history),
            'average_confidence': float(np.mean(list(self.confidence_scores.values()))) 
                                        if self.confidence_scores else 0.0
        }
    
    def get_regime_signal(self) -> Dict:
        """Get regime-based trading signal"""
        
        regime_signals = {
            'STRONG_BULL': {
                'action': 'BUY',
                'position_size': 0.10,  # 10% of portfolio
                'confidence': 0.95,
                'stop_loss_atr': 2.0,
                'take_profit_atr': 5.0
            },
            'BULL': {
                'action': 'BUY',
                'position_size': 0.06,
                'confidence': 0.85,
                'stop_loss_atr': 2.5,
                'take_profit_atr': 4.0
            },
            'NEUTRAL': {
                'action': 'HOLD',
                'position_size': 0.00,
                'confidence': 0.60,
                'stop_loss_atr': 2.0,
                'take_profit_atr': 2.0
            },
            'BEAR': {
                'action': 'SELL',
                'position_size': 0.06,
                'confidence': 0.85,
                'stop_loss_atr': 2.5,
                'take_profit_atr': 4.0
            },
            'STRONG_BEAR': {
                'action': 'SELL',
                'position_size': 0.10,
                'confidence': 0.95,
                'stop_loss_atr': 2.0,
                'take_profit_atr': 5.0
            }
        }
        
        signal = regime_signals.get(self.current_regime, regime_signals['NEUTRAL'])
        signal['regime'] = self.current_regime
        signal['timestamp'] = datetime.now().isoformat()
        
        return signal


logger.info("[REGIME DETECTION] HMM-based regime detector loaded")
