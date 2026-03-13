"""
Price Predictor
LSTM-based time-series prediction model
"""

import numpy as np
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass


@dataclass
class PredictionResult:
    """Price prediction result"""
    symbol: str
    current_price: float
    predicted_price: float
    confidence: float  # 0-1
    timeframe: str
    direction: str  # 'UP', 'DOWN', 'NEUTRAL'


class LSTMPredictor:
    """LSTM-based price predictor"""
    
    def __init__(self, lookback: int = 60, forecast_steps: int = 5):
        """
        Initialize predictor
        Args:
            lookback: Number of historical candles to use (default 60)
            forecast_steps: Number of candles to predict ahead (default 5)
        """
        self.lookback = lookback
        self.forecast_steps = forecast_steps
        self.model = None
        self.scaler = None
        self.history = {}
    
    def predict(self, symbol: str, prices: List[float], 
                current_price: float, timeframe: str = '1h') -> PredictionResult:
        """
        Predict next price movement
        Args:
            symbol: Trading pair (BTC/USD)
            prices: Historical price data
            current_price: Current market price
            timeframe: Candle timeframe
        Returns:
            PredictionResult with prediction and confidence
        """
        
        if len(prices) < self.lookback:
            # Not enough data, return neutral prediction
            return PredictionResult(
                symbol=symbol,
                current_price=current_price,
                predicted_price=current_price,
                confidence=0.0,
                timeframe=timeframe,
                direction='NEUTRAL'
            )
        
        # Get recent price history
        recent_prices = prices[-self.lookback:]
        
        # Normalize prices (simple min-max)
        min_price = min(recent_prices)
        max_price = max(recent_prices)
        price_range = max_price - min_price or 1
        
        normalized = [(p - min_price) / price_range for p in recent_prices]
        
        # Simple LSTM-like prediction: weighted moving average with momentum
        # In production, would use actual LSTM model from TensorFlow
        
        # Calculate trend
        short_ma = np.mean(recent_prices[-5:])
        long_ma = np.mean(recent_prices[-20:])
        momentum = short_ma - long_ma
        
        # Calculate volatility
        returns = np.diff(recent_prices) / recent_prices[:-1]
        volatility = np.std(returns)
        
        # Predict next price using momentum
        predicted_price = current_price * (1 + (momentum / long_ma) * 0.1)
        
        # Calculate confidence based on trend strength and volatility
        trend_strength = abs(momentum) / (long_ma or 1)
        confidence = min(0.95, (1 - volatility) * trend_strength)
        confidence = max(0.1, confidence)  # Minimum 10%, maximum 95%
        
        # Determine direction
        if predicted_price > current_price * 1.01:
            direction = 'UP'
        elif predicted_price < current_price * 0.99:
            direction = 'DOWN'
        else:
            direction = 'NEUTRAL'
        
        result = PredictionResult(
            symbol=symbol,
            current_price=current_price,
            predicted_price=predicted_price,
            confidence=confidence,
            timeframe=timeframe,
            direction=direction
        )
        
        # Store in history
        if symbol not in self.history:
            self.history[symbol] = []
        self.history[symbol].append(result)
        
        return result
    
    def predict_batch(self, predictions_data: List[Dict[str, Any]]) -> List[PredictionResult]:
        """Predict prices for multiple symbols"""
        results = []
        for data in predictions_data:
            result = self.predict(
                symbol=data['symbol'],
                prices=data['prices'],
                current_price=data['current_price'],
                timeframe=data.get('timeframe', '1h')
            )
            results.append(result)
        return results
    
    def get_ensemble_prediction(self, predictions: List[PredictionResult]) -> Dict[str, Any]:
        """Combine multiple predictions into ensemble"""
        if not predictions:
            return None
        
        # Weight by confidence
        total_weight = sum(p.confidence for p in predictions)
        weighted_price = sum(p.predicted_price * p.confidence for p in predictions) / (total_weight or 1)
        avg_confidence = sum(p.confidence for p in predictions) / len(predictions)
        
        # Majority vote on direction
        directions = [p.direction for p in predictions]
        direction_votes = {
            'UP': directions.count('UP'),
            'DOWN': directions.count('DOWN'),
            'NEUTRAL': directions.count('NEUTRAL')
        }
        majority_direction = max(direction_votes, key=direction_votes.get)
        
        return {
            'ensemble_price': weighted_price,
            'confidence': avg_confidence,
            'direction': majority_direction,
            'predictions_count': len(predictions)
        }
    
    def clear_history(self):
        """Clear prediction history"""
        self.history = {}


# Global predictor instance
_predictor = LSTMPredictor()


def predict_price(symbol: str, prices: List[float], 
                 current_price: float, timeframe: str = '1h') -> PredictionResult:
    """Predict next price movement"""
    return _predictor.predict(symbol, prices, current_price, timeframe)


def predict_batch(predictions_data: List[Dict[str, Any]]) -> List[PredictionResult]:
    """Predict prices for multiple symbols"""
    return _predictor.predict_batch(predictions_data)


def get_prediction_history(symbol: str = None) -> Dict[str, Any]:
    """Get prediction history"""
    if symbol:
        return {symbol: _predictor.history.get(symbol, [])}
    return _predictor.history
