"""
Market Scanner
Scans cryptocurrency markets for trading opportunities
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class MarketOpportunity:
    """Single market opportunity"""
    symbol: str
    exchange: str
    current_price: float
    volume_24h: float
    change_24h: float
    volatility: float
    trend_direction: str  # 'UP', 'DOWN'
    opportunity_score: float  # 0-100
    signals: List[str] = None


class MarketScanner:
    """Scans markets for trading opportunities"""
    
    def __init__(self, min_volume_usd: float = 100000, max_symbols: int = 100):
        """
        Initialize market scanner
        Args:
            min_volume_usd: Minimum 24h volume in USD
            max_symbols: Maximum symbols to track
        """
        self.min_volume_usd = min_volume_usd
        self.max_symbols = max_symbols
        
        # Top crypto symbols by market cap (simplified)
        self.top_symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT',
            'XRP/USDT', 'DOGE/USDT', 'AVAX/USDT', 'LINK/USDT', 'MATIC/USDT',
            'UNI/USDT', 'XLM/USDT', 'LTC/USDT', 'ATOM/USDT', 'ARB/USDT',
            'OP/USDT', 'APT/USDT', 'BLUR/USDT', 'FIT/USDT', 'FTT/USDT'
        ]
        
        self.scan_history = []
        self.opportunities = []
    
    def scan_symbol(self, symbol: str, prices: List[float], volumes: List[float],
                   exchange: str = 'binance', min_bars: int = 50) -> Dict[str, Any]:
        """
        Scan single symbol for opportunities
        Args:
            symbol: Trading pair (BTC/USD)
            prices: Historical prices
            volumes: Historical volumes
            exchange: Exchange name
            min_bars: Minimum bars for analysis
        Returns:
            Market opportunity data
        """
        if len(prices) < min_bars:
            return None
        
        recent_prices = prices[-min_bars:]
        recent_volumes = volumes[-min_bars:]
        
        current_price = recent_prices[-1]
        volume_24h = sum(recent_volumes[-24:]) if len(recent_volumes) >= 24 else sum(recent_volumes)
        
        # Calculate change 24h
        price_24h_ago = recent_prices[-24] if len(recent_prices) >= 24 else recent_prices[0]
        change_24h = (current_price - price_24h_ago) / price_24h_ago * 100
        
        # Calculate volatility
        returns = np.diff(recent_prices) / recent_prices[:-1]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        
        # Calculate trend
        sma_10 = np.mean(recent_prices[-10:])
        sma_50 = np.mean(recent_prices[-50:]) if len(recent_prices) >= 50 else np.mean(recent_prices)
        
        trend_direction = 'UP' if sma_10 > sma_50 else 'DOWN'
        
        # Detect signals
        signals = self._detect_signals(recent_prices, recent_volumes)
        
        # Calculate opportunity score
        score = self._calculate_opportunity_score(
            volatility, change_24h, volume_24h, trend_direction, signals
        )
        
        opportunity = MarketOpportunity(
            symbol=symbol,
            exchange=exchange,
            current_price=current_price,
            volume_24h=volume_24h,
            change_24h=change_24h,
            volatility=volatility,
            trend_direction=trend_direction,
            opportunity_score=score,
            signals=signals
        )
        
        return opportunity
    
    def _detect_signals(self, prices: List[float], volumes: List[float]) -> List[str]:
        """Detect technical signals"""
        signals = []
        
        recent_prices = prices[-20:]
        recent_volumes = volumes[-20:]
        
        # Breakout signal
        recent_high = max(recent_prices)
        recent_low = min(recent_prices)
        if prices[-1] == recent_high:
            signals.append('BREAKOUT_UP')
        elif prices[-1] == recent_low:
            signals.append('BREAKOUT_DOWN')
        
        # Volume spike
        avg_volume = np.mean(recent_volumes)
        if recent_volumes[-1] > avg_volume * 2:
            signals.append('VOLUME_SPIKE')
        
        # Momentum
        short_trend = np.mean(recent_prices[-5:])
        long_trend = np.mean(recent_prices)
        if short_trend > long_trend * 1.02:
            signals.append('MOMENTUM_UP')
        elif short_trend < long_trend * 0.98:
            signals.append('MOMENTUM_DOWN')
        
        return signals
    
    def _calculate_opportunity_score(self, volatility: float, change: float,
                                    volume: float, trend: str, signals: List[str]) -> float:
        """Calculate opportunity score (0-100)"""
        score = 0
        
        # Volatility score (higher volatility = more opportunity, but cap at 40%)
        vol_score = min(volatility * 50, 20)  # Max 20 points
        score += vol_score
        
        # Trend score
        trend_score = 10 if trend == 'UP' else 5
        score += trend_score
        
        # Volume score
        if volume > 1000000:
            score += 15
        elif volume > 500000:
            score += 10
        elif volume > 100000:
            score += 5
        
        # Signal bonus
        signal_bonus = len(signals) * 5  # 5 points per signal, max 25
        score += min(signal_bonus, 25)
        
        # Change score (be cautious with extreme moves)
        if 2 < change < 10:
            score += 15
        elif change > 10:
            score += 5  # Less favorable (might be pump)
        elif -5 < change < -1:
            score += 10  # Good reverse opportunity
        
        return min(score, 100)  # Cap at 100
    
    def scan_market(self, market_data: Dict[str, Any], limit: int = 20) -> List[MarketOpportunity]:
        """
        Scan entire market for opportunities
        Args:
            market_data: Market data for multiple symbols
            limit: Maximum opportunities to return
        Returns:
            Sorted list of opportunities
        """
        opportunities = []
        
        for symbol in self.top_symbols[:self.max_symbols]:
            if symbol in market_data:
                data = market_data[symbol]
                opp = self.scan_symbol(
                    symbol,
                    data.get('prices', []),
                    data.get('volumes', []),
                    exchange=data.get('exchange', 'binance')
                )
                
                if opp and opp.volume_24h >= self.min_volume_usd:
                    opportunities.append(opp)
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        self.opportunities = opportunities
        
        return opportunities[:limit]
    
    def get_filtered_opportunities(self, min_score: float = 50.0,
                                 trend_filter: str = None) -> List[MarketOpportunity]:
        """Get opportunities filtered by criteria"""
        filtered = self.opportunities
        
        if min_score:
            filtered = [o for o in filtered if o.opportunity_score >= min_score]
        
        if trend_filter:
            filtered = [o for o in filtered if o.trend_direction == trend_filter]
        
        return filtered
    
    def get_scan_status(self) -> Dict[str, Any]:
        """Get scan status"""
        return {
            'opportunities_found': len(self.opportunities),
            'top_opportunity': self.opportunities[0] if self.opportunities else None,
            'average_score': np.mean([o.opportunity_score for o in self.opportunities]),
            'last_scan': len(self.scan_history)
        }


# Convenience functions
_scanner = None


def initialize_scanner(min_volume: float = 100000) -> MarketScanner:
    """Initialize market scanner"""
    global _scanner
    _scanner = MarketScanner(min_volume_usd=min_volume)
    return _scanner


def get_scanner() -> MarketScanner:
    """Get market scanner"""
    global _scanner
    if _scanner is None:
        _scanner = MarketScanner()
    return _scanner


def scan_market(market_data: Dict[str, Any], limit: int = 20) -> List[MarketOpportunity]:
    """Scan market for opportunities"""
    return get_scanner().scan_market(market_data, limit)
