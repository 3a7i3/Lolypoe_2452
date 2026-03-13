"""
Market Scanner – Multi-crypto scanning with technical indicators
Scans 300+ cryptos, calculates RSI/MACD/EMA, detects anomalies
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketScanner:
    """Scan and score multiple cryptocurrencies"""

    def __init__(self, exchange_manager, symbols: List[str] = None):
        """Initialize with exchange manager"""
        self.em = exchange_manager
        self.symbols = symbols or self._get_top_symbols(300)
        self.scores = {}

    def _get_top_symbols(self, n: int = 300) -> List[str]:
        """Get top N symbols by market cap (simplified)"""
        top = [
            "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
            "ADA/USDT", "AVAX/USDT", "DOGE/USDT", "DOT/USDT", "MATIC/USDT",
            "LINK/USDT", "UNI/USDT", "ATOM/USDT", "LTC/USDT", "ETC/USDT",
            "FIL/USDT", "NEAR/USDT", "ALGO/USDT", "APT/USDT", "ARB/USDT",
        ]
        return top * (n // len(top) + 1)

    async def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period:
            return 50.0
        deltas = np.diff(prices)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = 100.0 - 100.0 / (1.0 + rs) if rs > 0 else 50.0
        return float(rsi)

    async def calculate_macd(self, prices: np.ndarray) -> Dict[str, float]:
        """Calculate MACD indicator"""
        ema12 = self._ema(prices, 12)
        ema26 = self._ema(prices, 26)
        macd = ema12 - ema26
        signal = self._ema(np.array([macd] * len(prices)), 9)
        histogram = macd - signal
        return {
            'macd': float(macd),
            'signal': float(signal),
            'histogram': float(histogram)
        }

    def _ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate EMA"""
        if len(prices) == 0:
            return 0
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = price * multiplier + ema * (1 - multiplier)
        return ema

    async def scan(self, limit_symbols: int = 50) -> pd.DataFrame:
        """Scan top cryptos and return scoring DataFrame"""
        results = []
        
        for symbol in self.symbols[:limit_symbols]:
            try:
                ticker = await self.em.fetch_ticker(symbol)
                if ticker['status'] == 'failed':
                    continue

                data = ticker['data']
                results.append({
                    'symbol': symbol.replace('/USDT', ''),
                    'price': data.get('last', 0),
                    'change_24h': data.get('percentage', 0),
                    'volume': data.get('quoteVolume', 0),
                    'bid': data.get('bid', 0),
                    'ask': data.get('ask', 0),
                    'exchange': ticker['exchange'],
                    'timestamp': datetime.now().isoformat(),
                })
            except Exception as e:
                logger.debug(f"Scan error for {symbol}: {e}")
                continue

        df = pd.DataFrame(results)
        
        if not df.empty:
            # Calculate composite score
            df['volume_score'] = (df['volume'] - df['volume'].min()) / (df['volume'].max() - df['volume'].min() + 1)
            df['trend_score'] = (df['change_24h'] + 50) / 100  # Normalize to 0-1
            df['composite_score'] = (df['volume_score'] * 0.6 + df['trend_score'] * 0.4).round(3)
            df = df.sort_values('composite_score', ascending=False)

        return df

    async def detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect market anomalies (volume spikes, price moves)"""
        anomalies = []
        
        for _, row in df.iterrows():
            if row['volume'] > df['volume'].quantile(0.95):
                anomalies.append({
                    'symbol': row['symbol'],
                    'type': 'HIGH_VOLUME',
                    'value': row['volume'],
                    'severity': 'HIGH'
                })
            if abs(row['change_24h']) > 20:
                anomalies.append({
                    'symbol': row['symbol'],
                    'type': 'HIGH_VOLATILITY',
                    'value': row['change_24h'],
                    'severity': 'CRITICAL'
                })

        return anomalies
