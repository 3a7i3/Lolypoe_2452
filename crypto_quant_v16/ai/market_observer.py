"""
Market Observer Agent – Surveys market for trends and anomalies
Detects high volume, price extremes, whale movements
"""

import logging
import pandas as pd
from typing import Dict, List, Any
from .advanced_analysis import AdvancedAnalysis

logger = logging.getLogger(__name__)


class MarketObserver:
    """Agent that analyzes market data and detects signals"""

    def __init__(self, name: str = "MarketObserver"):
        """Initialize agent"""
        self.name = name
        self.memory = []
        self.signals = []
        self.advanced = AdvancedAnalysis()

    async def analyze(self, market_data: pd.DataFrame) -> List[Dict]:
        """Analyze market data and generate signals"""
        signals = []
        if market_data.empty:
            return signals

        # Basic signals
        for _, row in market_data.iterrows():
            if row.get('volume', 0) > market_data['volume'].quantile(0.90):
                signals.append({
                    'symbol': row['symbol'],
                    'signal': 'HIGH_VOLUME',
                    'strength': 'STRONG',
                    'timestamp': pd.Timestamp.now()
                })
            if row.get('change_24h', 0) > 15:
                signals.append({
                    'symbol': row['symbol'],
                    'signal': 'PRICE_SPIKE_UP',
                    'strength': 'CRITICAL',
                    'value': row['change_24h']
                })
            elif row.get('change_24h', 0) < -15:
                signals.append({
                    'symbol': row['symbol'],
                    'signal': 'PRICE_SPIKE_DOWN',
                    'strength': 'CRITICAL',
                    'value': row['change_24h']
                })

        # Advanced analysis integration
        try:
            prices = market_data['price'].values if 'price' in market_data else None
            volumes = market_data['volume'].values if 'volume' in market_data else None
            tx_df = market_data[['timestamp', 'amount']] if 'amount' in market_data else pd.DataFrame()
            if prices is not None and volumes is not None:
                advanced_signals = self.advanced.detect_hedge_fund_patterns(prices, volumes, tx_df)
                for adv in advanced_signals:
                    adv['source'] = 'AdvancedAnalysis'
                signals.extend(advanced_signals)
        except Exception as e:
            logger.warning(f"Advanced analysis failed: {e}")

        self.memory.extend(signals)
        self.signals = signals
        logger.info(f"🔍 {self.name} detected {len(signals)} signals (basic + advanced)")
        return signals

    def get_hot_symbols(self, top_n: int = 5) -> List[str]:
        """Get most active symbols"""
        if not self.signals:
            return []
        
        signal_counts = pd.DataFrame(self.signals) \
            .groupby('symbol')['signal'].count() \
            .nlargest(top_n)
        
        return signal_counts.index.tolist()

    def memory_report(self) -> Dict[str, Any]:
        """Generate memory report"""
        if not self.memory:
            return {'total_signals': 0}
        
        df = pd.DataFrame(self.memory)
        return {
            'total_signals': len(self.memory),
            'signal_types': df['signal'].value_counts().to_dict(),
            'recent_signals': df.tail(10).to_dict('records')
        }
