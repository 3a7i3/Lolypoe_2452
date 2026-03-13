"""
Strategy Engine - Institutional-grade multi-strategy signal generation
Implements 5 core strategies: Trend Following, Mean Reversion, Volatility Breakout, 
Statistical Arbitrage, Market Making with advanced position sizing and risk management
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)

class InstitutionalStrategyEngine:
    """Generate institutional-grade trading signals from 5 core strategies"""
    
    def __init__(self):
        self.strategy_weights = config.STRATEGY_WEIGHTS
        self.strategy_params = config.STRATEGY_PARAMS
        self.max_position_size = config.MAX_POSITION_SIZE
        self.min_position_size = config.MIN_POSITION_SIZE
        self.position_history = {}
        self.strategy_performance = {s: {'wins': 0, 'losses': 0, 'pnl': 0} 
                                    for s in config.ENABLED_STRATEGIES}
        logger.info(f"✓ Institutional Strategy Engine initialized with {len(config.ENABLED_STRATEGIES)} strategies")
    
    async def generate_ensemble_signal(self, symbol: str, ohlcv_df: pd.DataFrame,
                                       features_df: pd.DataFrame,
                                       indicators: Dict, portfolio_value: float = 100000) -> Dict:
        """
        Generate ensemble signal from all 5 strategies with weighted voting
        Returns: {action: BUY/SELL/HOLD, position_size: %, confidence: 0-1, price_target: $, 
                  stop_loss: $, strategies: {strategy_details}}
        """
        try:
            signals = {}
            strategy_confidences = []
            
            # Generate signal from each strategy
            for strategy_name in config.ENABLED_STRATEGIES:
                try:
                    signal = await self._execute_strategy(strategy_name, symbol, ohlcv_df, 
                                                         features_df, indicators)
                    if signal:
                        signals[strategy_name] = signal
                        strategy_confidences.append(signal.get('confidence', 0) * 
                                                   self.strategy_weights.get(strategy_name, 0.2))
                except Exception as e:
                    logger.debug(f"Error in {strategy_name}: {e}")
            
            # Aggregate signals
            if not signals:
                return self._neutral_signal(symbol)
            
            # Ensemble voting
            signal = self._aggregate_signals(symbol, signals, strategy_confidences, portfolio_value)
            
            logger.debug(f"Ensemble signal for {symbol}: {signal['action']} "
                        f"(confidence: {signal['confidence']:.2%})")
            
            return signal
            
        except Exception as e:
            logger.error(f"Ensemble signal error for {symbol}: {e}")
            return self._neutral_signal(symbol)
    
    async def _execute_strategy(self, strategy_name: str, symbol: str, 
                               ohlcv_df: pd.DataFrame, features_df: pd.DataFrame,
                               indicators: Dict) -> Optional[Dict]:
        """Execute individual strategy"""
        if strategy_name == 'trend_following':
            return self._trend_following_strategy(symbol, ohlcv_df, indicators)
        elif strategy_name == 'mean_reversion':
            return self._mean_reversion_strategy(symbol, ohlcv_df, indicators)
        elif strategy_name == 'volatility_breakout':
            return self._volatility_breakout_strategy(symbol, ohlcv_df, indicators)
        elif strategy_name == 'statistical_arbitrage':
            return self._statistical_arbitrage_strategy(symbol, ohlcv_df, features_df, indicators)
        elif strategy_name == 'market_making':
            return self._market_making_strategy(symbol, ohlcv_df, indicators)
        
        return None
    
    def _trend_following_strategy(self, symbol: str, ohlcv_df: pd.DataFrame, 
                                  indicators: Dict) -> Optional[Dict]:
        """
        Trend Following Strategy
        BUY Signals: 
        - SMA20 > SMA50 > SMA200 (uptrend confirmation)
        - Price above SMA50
        - RSI between 30-70 (not overbought/oversold)
        - MACD histogram positive and growing
        
        SELL Signals: Opposite conditions
        """
        try:
            params = self.strategy_params['trend_following']
            
            sma_short = indicators.get('sma_20', 0)
            sma_long = indicators.get('sma_50', 0)
            sma_200 = indicators.get('sma_200', 0)
            rsi = indicators.get('rsi_14', 50)
            macd_hist = indicators.get('macd_histogram', 0)
            current_price = ohlcv_df['close'].iloc[-1]
            
            confidence = 0.0
            action = None
            reason = ""
            
            # BUY Logic
            if (sma_short > sma_long > sma_200 and current_price > sma_long and 
                params['rsi_threshold'] < rsi < (100 - params['rsi_threshold']) and 
                macd_hist > 0):
                
                # Confidence based on trend strength
                trend_strength = (sma_short - sma_200) / sma_200
                rsi_score = min(abs(rsi - 50) / 20, 1.0)  # 0-1 scale
                confidence = min(trend_strength + rsi_score, 1.0) / 2
                
                action = 'BUY'
                reason = f"Strong uptrend: SMA alignment + RSI {rsi:.0f} + MACD positive"
            
            # SELL Logic
            elif (sma_short < sma_long < sma_200 or current_price < sma_long and 
                  macd_hist < 0):
                
                trend_strength = (sma_200 - sma_short) / sma_200
                confidence = min(trend_strength, 1.0)
                
                action = 'SELL'
                reason = f"Downtrend: SMA alignment broken + MACD negative"
            
            if action:
                return {
                    'strategy': 'trend_following',
                    'action': action,
                    'confidence': max(confidence, 0.3),  # Min 30% confidence
                    'reason': reason,
                    'entry_price': current_price,
                    'stop_loss': current_price * (1 - params['stop_loss']) if action == 'BUY' else current_price * (1 + params['stop_loss']),
                    'take_profit': current_price * (1 + params['take_profit']) if action == 'BUY' else current_price * (1 - params['take_profit']),
                    'min_volume': params['min_volume']
                }
            
        except Exception as e:
            logger.debug(f"Trend following error: {e}")
        
        return None
    
    def _mean_reversion_strategy(self, symbol: str, ohlcv_df: pd.DataFrame, 
                                indicators: Dict) -> Optional[Dict]:
        """
        Mean Reversion Strategy
        BUY: Price at Bollinger Lower Band + RSI < Oversold + Moving away from Low
        SELL: Price at Bollinger Upper Band + RSI > Overbought
        """
        try:
            params = self.strategy_params['mean_reversion']
            
            current_price = ohlcv_df['close'].iloc[-1]
            bb_upper = indicators.get('bb_upper_20', current_price)
            bb_lower = indicators.get('bb_lower_20', current_price)
            bb_middle = indicators.get('bb_middle_20', current_price)
            rsi = indicators.get('rsi_14', 50)
            
            confidence = 0.0
            action = None
            reason = ""
            
            # Distance from Bollinger Bands (0-1)
            if bb_upper > bb_lower:
                bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            else:
                bb_position = 0.5
            
            # BUY Logic - Mean reversion up
            if current_price < bb_middle and bb_position < 0.3 and rsi < params['rsi_oversold']:
                distance_from_lower = (current_price - bb_lower) / (bb_middle - bb_lower + 1e-8)
                confidence = min(1.0 - distance_from_lower, 1.0) * 0.8
                
                action = 'BUY'
                reason = f"Mean reversion: Price near lower BB + RSI {rsi:.0f} oversold"
            
            # SELL Logic - Mean reversion down
            elif current_price > bb_middle and bb_position > 0.7 and rsi > params['rsi_overbought']:
                distance_from_upper = (bb_upper - current_price) / (bb_upper - bb_middle + 1e-8)
                confidence = min(distance_from_upper, 1.0) * 0.8
                
                action = 'SELL'
                reason = f"Mean reversion: Price near upper BB + RSI {rsi:.0f} overbought"
            
            if action:
                reversion_period = params['mean_reversion_period']
                return {
                    'strategy': 'mean_reversion',
                    'action': action,
                    'confidence': max(confidence, 0.35),
                    'reason': reason,
                    'entry_price': current_price,
                    'target_price': bb_middle,
                    'stop_loss': bb_upper if action == 'BUY' else bb_lower,
                    'take_profit': current_price * (1 + reversion_period * 0.001) if action == 'BUY' else current_price * (1 - reversion_period * 0.001),
                    'timeframe': reversion_period
                }
            
        except Exception as e:
            logger.debug(f"Mean reversion error: {e}")
        
        return None
    
    def _volatility_breakout_strategy(self, symbol: str, ohlcv_df: pd.DataFrame, 
                                      indicators: Dict) -> Optional[Dict]:
        """
        Volatility Breakout Strategy
        Trades breakouts above/below ATR + recent range
        BUY: Price breaks above recent high + ATR expanding
        SELL: Price breaks below recent low + ATR expanding
        """
        try:
            params = self.strategy_params['volatility_breakout']
            
            current_price = ohlcv_df['close'].iloc[-1]
            atr = indicators.get('atr_14', 0)
            
            # Calculate recent range
            lookback = params['breakout_lookback']
            recent_high = ohlcv_df['high'].tail(lookback).max()
            recent_low = ohlcv_df['low'].tail(lookback).min()
            recent_range = recent_high - recent_low
            
            # Historical ATR for comparison
            prev_atr = indicators.get('atr_21', atr)  # Use larger period for comparison
            volatility_ratio = atr / (prev_atr + 1e-8)
            
            confidence = 0.0
            action = None
            reason = ""
            
            # BUY: Breakout above with expanding volatility
            if (current_price > recent_high and 
                volatility_ratio > params['volume_threshold'] and
                atr > 0):
                
                breakout_distance = (current_price - recent_high) / (recent_range + 1e-8)
                confidence = min(0.3 + volatility_ratio * 0.3, 1.0)
                
                action = 'BUY'
                reason = f"Volatility breakout: Price above range + ATR {volatility_ratio:.2f}x"
            
            # SELL: Breakout below with expanding volatility
            elif (current_price < recent_low and 
                  volatility_ratio > params['volume_threshold']):
                
                confidence = min(0.3 + volatility_ratio * 0.3, 1.0)
                
                action = 'SELL'
                reason = f"Volatility breakout down: Price below range + ATR expanding"
            
            if action:
                return {
                    'strategy': 'volatility_breakout',
                    'action': action,
                    'confidence': max(confidence, 0.35),
                    'reason': reason,
                    'entry_price': current_price,
                    'stop_loss': recent_low if action == 'BUY' else recent_high,
                    'take_profit': current_price + (atr * params['atr_threshold']) if action == 'BUY' else current_price - (atr * params['atr_threshold']),
                    'atr_multiple': params['atr_threshold'],
                    'volatility_expansion': volatility_ratio
                }
            
        except Exception as e:
            logger.debug(f"Volatility breakout error: {e}")
        
        return None
    
    def _statistical_arbitrage_strategy(self, symbol: str, ohlcv_df: pd.DataFrame, 
                                       features_df: pd.DataFrame, indicators: Dict) -> Optional[Dict]:
        """
        Statistical Arbitrage Strategy
        Tracks correlated pairs and mean-reverting spreads
        Requires correlation analysis and z-score of pair spread
        """
        try:
            params = self.strategy_params['statistical_arbitrage']
            
            current_price = ohlcv_df['close'].iloc[-1]
            
            confidence = 0.0
            action = None
            reason = ""
            
            # Statistical arbitrage relies on pair correlation
            # Use z-score of recent returns for mean reversion
            if len(ohlcv_df) > params['hedge_ratio_lookback']:
                returns = ohlcv_df['close'].pct_change().tail(params['hedge_ratio_lookback'])
                z_score = (returns.iloc[-1] - returns.mean()) / (returns.std() + 1e-8)
                
                # BUY if statistically cheap (negative z-score)
                if z_score < -params['zscore_threshold']:
                    confidence = min(abs(z_score) / 3.0, 1.0)  # Normalize to max 3 sigma
                    action = 'BUY'
                    reason = f"Statistical arbitrage: Z-score {z_score:.2f} (oversold)"
                
                # SELL if statistically expensive (positive z-score)
                elif z_score > params['zscore_threshold']:
                    confidence = min(abs(z_score) / 3.0, 1.0)
                    action = 'SELL'
                    reason = f"Statistical arbitrage: Z-score {z_score:.2f} (overbought)"
            
            if action:
                prediction_window = 5  # periods ahead
                return {
                    'strategy': 'statistical_arbitrage',
                    'action': action,
                    'confidence': max(confidence, 0.4),
                    'reason': reason,
                    'entry_price': current_price,
                    'z_score': z_score if 'z_score' in locals() else 0,
                    'stop_loss': current_price * (1 - 0.03) if action == 'BUY' else current_price * (1 + 0.03),
                    'take_profit': current_price * (1 + 0.05) if action == 'BUY' else current_price * (1 - 0.05),
                    'prediction_window': prediction_window
                }
            
        except Exception as e:
            logger.debug(f"Statistical arbitrage error: {e}")
        
        return None
    
    def _market_making_strategy(self, symbol: str, ohlcv_df: pd.DataFrame, 
                               indicators: Dict) -> Optional[Dict]:
        """
        Market Making Strategy
        Provides liquidity by placing bids and asks around current price
        Position: Small (inventory limit), frequent adjustments
        """
        try:
            params = self.strategy_params['market_making']
            
            current_price = ohlcv_df['close'].iloc[-1]
            bid_ask_spread = indicators.get('bid_ask_spread', 0.002)
            recent_volatility = indicators.get('volatility_10', 0.01)
            
            # Adjust spread based on volatility
            target_spread = max(params['bid_ask_spread_target'], recent_volatility * 2)
            
            # Bid and ask prices
            bid_price = current_price * (1 - target_spread / 2)
            ask_price = current_price * (1 + target_spread / 2)
            
            confidence = 0.5  # Market making has consistent confidence
            
            return {
                'strategy': 'market_making',
                'action': 'MARKET_MAKE',
                'confidence': confidence,
                'reason': f"Market making: Provide liquidity with {target_spread:.2%} spread",
                'bid_price': bid_price,
                'ask_price': ask_price,
                'bid_size': params['inventory_limit'] * 0.5,  # 50% of limit
                'ask_size': params['inventory_limit'] * 0.5,
                'inventory_position': params['inventory_limit'],
                'refresh_time': params['order_refresh_time'],
                'volatility_adjusted': True
            }
            
        except Exception as e:
            logger.debug(f"Market making error: {e}")
        
        return None
    
    def _aggregate_signals(self, symbol: str, signals: Dict, 
                          confidences: List[float], portfolio_value: float) -> Dict:
        """Aggregate signals from all strategies using weighted voting"""
        try:
            # Calculate weighted consensus
            buy_signals = sum(1 for s in signals.values() if s.get('action') == 'BUY')
            sell_signals = sum(1 for s in signals.values() if s.get('action') == 'SELL')
            
            total_confidence = sum(confidences) if confidences else 0
            avg_confidence = total_confidence / len(signals) if signals else 0
            
            action = None
            reason = ""
            
            # Majority voting
            if buy_signals > sell_signals:
                action = 'BUY'
                reason = f"{buy_signals}/{len(signals)} strategies bullish"
            elif sell_signals > buy_signals:
                action = 'SELL'
                reason = f"{sell_signals}/{len(signals)} strategies bearish"
            else:
                return self._neutral_signal(symbol)
            
            # Calculate position size based on confidence
            position_size = self.min_position_size + (avg_confidence * 
                           (self.max_position_size - self.min_position_size))
            
            # Get price target and stops from majority strategy
            majority_strategy = max(signals.items(), key=lambda x: x[1].get('confidence', 0))
            majority_signal = majority_strategy[1]
            
            return {
                'symbol': symbol,
                'action': action,
                'confidence': avg_confidence,
                'position_size': position_size,
                'entry_price': majority_signal.get('entry_price', 0),
                'stop_loss': majority_signal.get('stop_loss', 0),
                'take_profit': majority_signal.get('take_profit', 0),
                'reason': reason,
                'strategies': {k: {'confidence': v.get('confidence'), 
                                  'reason': v.get('reason')} 
                              for k, v in signals.items()},
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Signal aggregation error: {e}")
            return self._neutral_signal(symbol)
    
    @staticmethod
    def _neutral_signal(symbol: str) -> Dict:
        """Return neutral/hold signal"""
        return {
            'symbol': symbol,
            'action': 'HOLD',
            'confidence': 0.0,
            'position_size': 0.0,
            'reason': 'No clear signal',
            'strategies': {},
            'timestamp': datetime.now().isoformat()
        }


print("[STRATEGY ENGINE] Institutional trading strategies loaded (5 core strategies + ensemble)")
                confidence = 0.7
                action = 'BUY'
            elif price < low * 0.98:
                confidence = 0.6
                action = 'SELL'
            
            if action:
                return {
                    'action': action,
                    'confidence': confidence,
                    'reason': 'Breakout signal'
                }
            
        except Exception as e:
            logger.debug(f"Breakout error: {e}")
        
        return None
    
    def volatility_trading(self, symbol: str, market_data: Dict, indicators: Dict) -> Optional[Dict]:
        """
        Volatility Trading Strategy
        Trade when ATR > threshold (high volatility opportunity)
        """
        try:
            atr = indicators.get('atr_14', 0)
            rsi = indicators.get('rsi_14', 50)
            
            confidence = 0.0
            action = None
            
            if atr > 2.0:  # High volatility
                if rsi < 50:
                    confidence = 0.5
                    action = 'BUY'
                else:
                    confidence = 0.5
                    action = 'SELL'
            
            if action:
                return {
                    'action': action,
                    'confidence': confidence,
                    'reason': 'Volatility trading signal'
                }
            
        except Exception as e:
            logger.debug(f"Volatility trading error: {e}")
        
        return None
    
    def momentum(self, symbol: str, market_data: Dict, indicators: Dict) -> Optional[Dict]:
        """
        Momentum Strategy
        Detect strong uptrends/downtrends
        """
        try:
            macd = indicators.get('macd', {})
            rsi = indicators.get('rsi_14', 50)
            
            confidence = 0.0
            action = None
            
            if macd.get('histogram', 0) > 0 and rsi > 50:
                confidence = 0.6
                action = 'BUY'
            elif macd.get('histogram', 0) < 0 and rsi < 50:
                confidence = 0.6
                action = 'SELL'
            
            if action:
                return {
                    'action': action,
                    'confidence': confidence,
                    'reason': 'Momentum signal'
                }
            
        except Exception as e:
            logger.debug(f"Momentum error: {e}")
        
        return None
    
    def statistical_arbitrage(self, symbol: str, market_data: Dict, indicators: Dict) -> Optional[Dict]:
        """
        Statistical Arbitrage Strategy
        Compare with correlated assets
        """
        try:
            # Simplified stat arb
            rsi = indicators.get('rsi_14', 50)
            
            if abs(50 - rsi) > 15:
                action = 'BUY' if rsi < 35 else 'SELL'
                confidence = 0.4
                
                return {
                    'action': action,
                    'confidence': confidence,
                    'reason': 'Statistical arbitrage signal'
                }
            
        except Exception as e:
            logger.debug(f"Statistical arbitrage error: {e}")
        
        return None
