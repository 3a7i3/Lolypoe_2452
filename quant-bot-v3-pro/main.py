#!/usr/bin/env python3
"""
QUANT BOT v3 PRO - Trading Bot Principal
========================================
Cerveau orchestrateur du bot quantitatif
"""

from core.scanner import scan_market
from core.strategy_engine import generate_trade_signal
from core.trade_executor import execute_trade
from core.risk_manager import validate_trade, reset_trade_count, open_position, update_trailing_stop
from core.advanced_analytics import AdvancedAnalytics
from utils.logger import logger
from config import SYMBOLS

# Initialiser les analytics avancees
analytics = AdvancedAnalytics()

def run():
    """Lance le cycle de trading principal avec analytics avancees."""
    try:
        logger.info("[START] Cycle de trading")
        reset_trade_count()
        
        # 1. Scann le marche
        market_data = scan_market()
        
        if not market_data:
            logger.warning("Aucune donnee de marche")
            return
        
        # 2. Parcourt chaque symbol
        for symbol, data in market_data.items():
            try:
                # 3. ANALYTICS AVANCEES
                predictions = analytics.predict_price(data, periods_ahead=3)
                trend = analytics.detect_trend(data)
                volatility = analytics.calculate_volatility(data)
                
                price = float(data['CLOSE'].iloc[-1])
                
                # Log analytics
                if trend['trend'] != 'UNKNOWN':
                    logger.info(f"{symbol} - Tendance: {trend['trend']} | Vol: {volatility['volatility_level']} | Pred: ${predictions[0]:.2f}")
                
                # 4. Genere le signal
                signal = generate_trade_signal(data)
                
                # 5. Valide le trade avec trailing stop
                if validate_trade(signal, symbol):
                    # Ouvrir position avec trailing stop
                    open_position(symbol, price)
                    # Execute le trade
                    execute_trade(symbol, signal, price)
                else:
                    # Mettre a jour trailing stop existant
                    update_trailing_stop(symbol, price)
                    logger.debug(f"Trade non valide: {symbol} - {signal}")
            
            except Exception as e:
                logger.error(f"Erreur traitement {symbol}: {e}")
        
        logger.info("[END] Cycle de trading termine")
    
    except Exception as e:
        logger.error(f"Erreur cycle principal: {e}")

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("QUANT BOT v3 PRO Demarrage")
    logger.info("=" * 50)
    run()
    logger.info("QUANT BOT v3 PRO Arret")
