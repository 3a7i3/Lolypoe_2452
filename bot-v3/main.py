from core.market_data import get_market_data
from core.indicators import calculate_indicators
from core.strategy import generate_signal
from core.risk_management import check_risk, increment_trade_count, open_position, update_trailing_stop
from core.logger import log_trade, logger
from core.advanced_analytics import AdvancedAnalytics
from config import SYMBOLS

# Initialiser les analytics avancees
analytics = AdvancedAnalytics()

def run_bot():
    """Cerveau principal du bot - orchestre tout avec analytics avancees."""
    
    for symbol in SYMBOLS:
        try:
            # 1. Recuperer les donnees
            logger.info(f"Recuperation donnees {symbol}...")
            data = get_market_data(symbol)
            
            if data is None or data.empty:
                logger.warning(f"Pas de donnees pour {symbol}")
                continue
            
            # 2. Calculer les indicateurs
            data = calculate_indicators(data)
            
            # 3. ANALYTICS AVANCEES
            logger.debug(f"Analytics: Prediction de prix pour {symbol}...")
            predictions = analytics.predict_price(data, periods_ahead=3)
            
            trend = analytics.detect_trend(data)
            volatility = analytics.calculate_volatility(data)
            
            price = data['Close'].iloc[-1].item()
            
            # Afficher tendance et volatilite
            if trend['trend'] != 'UNKNOWN':
                logger.info(f"{symbol} - Tendance: {trend['trend']} (Force: {trend['strength']:.1%}), Vol: {volatility['volatility_level']}")
            
            # 4. Generer le signal
            signal = generate_signal(data)
            
            # 5. Verifier le risque + Trailing Stop
            if check_risk(signal):
                # Ouvrir position avec trailing stop
                open_position(symbol, price)
                log_trade(signal, price)
                increment_trade_count()
                print(f"[SIGNAL] {symbol} - {signal} @ ${price:.2f} | Pred: ${predictions[0]:.2f} | {trend['trend']}")
            else:
                # Mettre a jour trailing stop existant
                if update_trailing_stop(symbol, price):
                    logger.warning(f"Trailing stop applique: {symbol}")
                print(f"[HOLD] {symbol} - {signal}")
        
        except Exception as e:
            logger.error(f"Erreur pour {symbol}: {e}")

if __name__ == "__main__":
    logger.info("[*] Bot demarrage")
    run_bot()
    logger.info("[*] Bot arret")
