"""
AdvancedAnalysis – Détection avancée de patterns pour MarketObserver
Fournit des signaux supplémentaires (ex : whale moves, anomalies volume/prix)
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any

class AdvancedAnalysis:
    """Analyse avancée pour la détection de signaux de marché"""
    def __init__(self):
        pass

    def detect_hedge_fund_patterns(self, prices, volumes, tx_df=None) -> List[Dict[str, Any]]:
        signals = []
        # Whale move: spike de volume + variation de prix > 8%
        if len(prices) > 10 and len(volumes) > 10:
            price_change = (prices[-1] - prices[-10]) / max(prices[-10], 1e-8) * 100
            volume_spike = volumes[-1] > np.percentile(volumes, 95)
            if abs(price_change) > 8 and volume_spike:
                signals.append({
                    'signal': 'WHALE_MOVE',
                    'strength': 'CRITICAL',
                    'price_change_pct': price_change,
                    'volume': volumes[-1],
                })
        # Anomalie de volume isolée
        if len(volumes) > 20:
            mean_vol = np.mean(volumes[:-5])
            if mean_vol > 0 and volumes[-1] > 2.5 * mean_vol:
                signals.append({
                    'signal': 'VOLUME_ANOMALY',
                    'strength': 'HIGH',
                    'volume': volumes[-1],
                })
        # Pattern custom : chute brutale
        if len(prices) > 5:
            drop = (prices[-2] - prices[-1]) / max(prices[-2], 1e-8) * 100
            if drop > 7:
                signals.append({
                    'signal': 'SUDDEN_DROP',
                    'strength': 'WARNING',
                    'drop_pct': drop,
                })
        # Placeholder pour d'autres patterns (ex : analyse tx_df)
        # ...
        return signals
