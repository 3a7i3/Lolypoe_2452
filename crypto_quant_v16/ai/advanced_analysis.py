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
        return signals

class AdvancedMarketAnalysis:
    """
    AI Research Agent: Analyse avancée du marché pour le pipeline quant.
    Produit un rapport structuré pour strategy_farm, risk_engine, portfolio_engine, execution_engine.
    """
    def __init__(self, df):
        self.df = df

    # --------------------------------
    # Volatility analysis
    # --------------------------------
    def volatility_analysis(self):
        returns = self.df["close"].pct_change()
        vol = returns.rolling(30).std().iloc[-1]
        if vol > 0.04:
            regime = "high_volatility"
        else:
            regime = "normal"
        return {
            "volatility_value": float(vol),
            "volatility_regime": regime
        }

    # --------------------------------
    # Trend strength
    # --------------------------------
    def trend_analysis(self):
        ma50 = self.df["close"].rolling(50).mean().iloc[-1]
        ma200 = self.df["close"].rolling(200).mean().iloc[-1]
        if ma50 > ma200:
            trend = "bull"
        else:
            trend = "bear"
        strength = abs(ma50 - ma200) / ma200
        return {
            "trend": trend,
            "trend_strength": float(strength)
        }

    # --------------------------------
    # Liquidity analysis
    # --------------------------------
    def liquidity_analysis(self):
        volume = self.df["volume"].rolling(30).mean().iloc[-1]
        if volume < self.df["volume"].quantile(0.25):
            liquidity = "low"
        else:
            liquidity = "normal"
        return {
            "liquidity": liquidity,
            "avg_volume": float(volume)
        }

    # --------------------------------
    # Crash probability
    # --------------------------------
    def crash_risk_estimator(self):
        returns = self.df["close"].pct_change()
        volatility = returns.std()
        downside = returns[returns < 0].std()
        crash_risk = downside / volatility if volatility > 0 else 0
        return {
            "crash_probability": float(crash_risk)
        }

    # --------------------------------
    # Market regime
    # --------------------------------
    def market_regime_detection(self):
        vol = self.volatility_analysis()["volatility_regime"]
        trend = self.trend_analysis()["trend"]
        if trend == "bull" and vol == "normal":
            regime = "bull_trend"
        elif trend == "bear" and vol == "high_volatility":
            regime = "panic_bear"
        else:
            regime = "sideways"
        return regime

    # --------------------------------
    # Whale activity detection (placeholder)
    # --------------------------------
    def whale_activity_detection(self):
        # À implémenter : détection de gros ordres, wallet tracking, etc.
        # Retourne un statut fictif pour l'instant
        return {"whale_activity": "accumulation"}

    # --------------------------------
    # Final report
    # --------------------------------
    def generate_market_report(self):
        report = {}
        report.update(self.volatility_analysis())
        report.update(self.trend_analysis())
        report.update(self.liquidity_analysis())
        report.update(self.crash_risk_estimator())
        report["market_regime"] = self.market_regime_detection()
        report.update(self.whale_activity_detection())
        return report
