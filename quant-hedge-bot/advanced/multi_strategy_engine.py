"""Multi-Strategy Trading Engine"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from utils.logger import logger

class MultiStrategyEngine:
    """
    Multiple Trading Strategies:
    - Trend Following
    - Mean Reversion
    - Breakout Trading
    - Volatility Trading
    - Market Making
    """
    
    @staticmethod
    def trend_following(data: pd.DataFrame) -> Dict:
        """
        Trend Following Strategy
        ========================
        BUY: SMA20 > SMA50 AND Price > SMA20 AND Momentum >0
        SELL: SMA20 < SMA50 OR Price < SMA20 OR Momentum < 0
        """
        close = data['Close'].iloc[-1]
        sma20 = data['Close'].rolling(20).mean().iloc[-1]
        sma50 = data['Close'].rolling(50).mean().iloc[-1]
        momentum = data['Close'].pct_change().iloc[-1]
        
        score = 0
        max_score = 3
        
        if sma20 > sma50:
            score += 1
        if close > sma20:
            score += 1
        if momentum > 0:
            score += 1
        
        confidence = score / max_score
        action = 'BUY' if score >= 2 else ('SELL' if score <= 1 else 'HOLD')
        
        return {'action': action, 'confidence': confidence, 'score': score}
    
    @staticmethod
    def mean_reversion(data: pd.DataFrame) -> Dict:
        """
        Mean Reversion Strategy
        =======================
        BUY: RSI < 30 AND Price < Bollinger Lower Band
        SELL: RSI > 70 AND Price > Bollinger Upper Band
        """
        rsi = data['RSI'].iloc[-1] if 'RSI' in data else 50
        bb_upper = data['BB_Upper'].iloc[-1] if 'BB_Upper' in data else data['Close'].iloc[-1] * 1.02
        bb_lower = data['BB_Lower'].iloc[-1] if 'BB_Lower' in data else data['Close'].iloc[-1] * 0.98
        close = data['Close'].iloc[-1]
        
        score = 0
        max_score = 2
        
        if rsi < 30 and close < bb_lower:
            score = 2
            action = 'BUY'
        elif rsi > 70 and close > bb_upper:
            score = -2
            action = 'SELL'
        else:
            action = 'HOLD'
        
        confidence = abs(score) / max_score if max_score > 0 else 0
        
        return {'action': action, 'confidence': confidence, 'score': score}
    
    @staticmethod
    def breakout(data: pd.DataFrame) -> Dict:
        """
        Breakout Trading Strategy
        ==========================
        BUY: Price breaks above 20-period high AND Volume > Avg Volume
        SELL: Price breaks below 20-period low AND Volume > Avg Volume
        """
        close = data['Close'].iloc[-1]
        high_20 = data['Close'].rolling(20).max().iloc[-1]
        low_20 = data['Close'].rolling(20).min().iloc[-1]
        volume = data['Volume'].iloc[-1] if 'Volume' in data else 1000000
        avg_volume = data['Volume'].rolling(20).mean().iloc[-1] if 'Volume' in data else 1000000
        
        score = 0
        max_score = 2
        confidence = 0
        
        if close > high_20 * 1.01 and volume > avg_volume:
            score = 2
            action = 'BUY'
            confidence = 0.8
        elif close < low_20 * 0.99 and volume > avg_volume:
            score = -2
            action = 'SELL'
            confidence = 0.8
        else:
            action = 'HOLD'
            confidence = 0.3
        
        return {'action': action, 'confidence': confidence, 'score': score}
    
    @staticmethod
    def volatility_trading(data: pd.DataFrame) -> Dict:
        """
        Volatility Trading Strategy
        ============================
        BUY: ATR increases AND RSI < 50 (expansion + oversold)
        SELL: ATR decreases AND RSI > 50 (contraction + overbought)
        """
        atr_current = data['ATR'].iloc[-1] if 'ATR' in data else 1
        atr_prev = data['ATR'].iloc[-2] if len(data) > 1 and 'ATR' in data else 1
        rsi = data['RSI'].iloc[-1] if 'RSI' in data else 50
        
        score = 0
        
        if atr_current > atr_prev * 1.05 and rsi < 50:
            score = 2
            action = 'BUY'
        elif atr_current < atr_prev * 0.95 and rsi > 50:
            score = -2
            action = 'SELL'
        else:
            action = 'HOLD'
        
        confidence = abs(score) / 2
        
        return {'action': action, 'confidence': confidence, 'score': score}
    
    @staticmethod
    def market_making(data: pd.DataFrame) -> Dict:
        """
        Market Making Strategy
        ======================
        PLACE ORDERS: At bid/ask spread
        Close when spread closes or max hold time reached
        """
        close = data['Close'].iloc[-1]
        atr = data['ATR'].iloc[-1] if 'ATR' in data else close * 0.01
        
        # Simple market making: place orders at spread
        bid = close - (atr * 0.5)
        ask = close + (atr * 0.5)
        
        # Action based on inventory
        action = 'HOLD'  # Market makers typically hold balanced inventory
        confidence = 0.5
        
        return {
            'action': action,
            'confidence': confidence,
            'bid': bid,
            'ask': ask,
            'spread': ask - bid
        }
    
    def list_strategies(self) -> list:
        """Return list of available strategies."""
        return [
            'trend_following',
            'mean_reversion',
            'breakout',
            'volatility_trading',
            'market_making'
        ]
    
    def backtest_strategy(self, strategy_name: str, data: pd.DataFrame) -> Dict:
        """Backtest a specific strategy on historical data."""
        strategy_func = getattr(self, strategy_name, None)
        
        if not strategy_func:
            logger.error(f"Strategy {strategy_name} not found")
            return {}
        
        results = []
        for i in range(len(data)):
            window = data.iloc[:i+1]
            if len(window) < 50:
                continue
            
            signal = strategy_func(window)
            results.append({
                'date': data.index[i],
                'signal': signal['action'],
                'confidence': signal['confidence'],
                'price': data['Close'].iloc[i]
            })
        
        return pd.DataFrame(results)
