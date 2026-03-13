"""
Script de test des 5 fonctionnalites avancees.
"""

import sys
sys.path.insert(0, '/Users/WINDOWS/crypto_ai_terminal/bot-v3')

from core.advanced_analytics import AdvancedAnalytics
from core.market_data import get_market_data
from core.logger import logger

def test_advanced_features():
    """Test toutes les 5 fonctionnalites avancees."""
    
    logger.info("=" * 60)
    logger.info("TEST DES 5 FONCTIONNALITES AVANCEES")
    logger.info("=" * 60)
    
    # Initialiser le module
    analytics = AdvancedAnalytics()
    
    # Obtenir donnees de test
    logger.info("\n[1] Recuperation des donnees...")
    # Utiliser l'intvalle 1d (quotidien) pour les longues periodes
    data = get_market_data("BTC-USD", interval="1d", period="6mo")
    if data is None or data.empty:
        logger.error("Impossible de recuperer les donnees")
        return
    
    logger.info(f"Donnees chargees: {len(data)} periodes")
    
    # ===== 1. IA PREDICTIVE =====
    logger.info("\n" + "="*60)
    logger.info("1️⃣ IA PREDICTIVE - predict_price()")
    logger.info("="*60)
    predictions = analytics.predict_price(data, periods_ahead=5)
    if predictions:
        logger.info(f"Predictions (5 prochaines periodes):")
        for i, pred in enumerate(predictions, 1):
            logger.info(f"   {i}. ${pred:.2f}")
    
    # ===== 2. DETECTION DE TENDANCE =====
    logger.info("\n" + "="*60)
    logger.info("2️⃣ DETECTION DE TENDANCE - detect_trend()")
    logger.info("="*60)
    trend_analysis = analytics.detect_trend(data)
    logger.info(f"Tendance: {trend_analysis['trend']}")
    logger.info(f"Force: {trend_analysis['strength']:.2%}")
    logger.info(f"Details:")
    for key, value in trend_analysis['details'].items():
        logger.info(f"   {key}: {value:.2f}")
    
    # ===== 3. ANALYSE VOLATILITE =====
    logger.info("\n" + "="*60)
    logger.info("3️⃣ ANALYSE VOLATILITE - calculate_volatility()")
    logger.info("="*60)
    volatility = analytics.calculate_volatility(data)
    logger.info(f"ATR: ${volatility['atr']:.2f}")
    logger.info(f"Std Dev: {volatility['std_dev']:.4f}")
    logger.info(f"ATR %: {volatility['atr_percent']:.2f}%")
    logger.info(f"Niveau de volatilite: {volatility['volatility_level']}")
    
    # ===== 4. BACKTESTING =====
    logger.info("\n" + "="*60)
    logger.info("4️⃣ BACKTESTING - run_backtest()")
    logger.info("="*60)
    
    # Simple signal function pour le backtest
    def simple_signal(data):
        if len(data) < 50:
            return "HOLD"
        sma20 = data['Close'].rolling(20).mean().iloc[-1]
        sma50 = data['Close'].rolling(50).mean().iloc[-1]
        if sma20 > sma50:
            return "BUY"
        elif sma20 < sma50:
            return "SELL"
        return "HOLD"
    
    backtest_results = analytics.run_backtest(data, simple_signal)
    if backtest_results:
        logger.info(f"Capital initial: ${backtest_results['initial_capital']:.2f}")
        logger.info(f"Capital final: ${backtest_results['final_capital']:.2f}")
        logger.info(f"ROI: {backtest_results['total_return_percent']:.2f}%")
        logger.info(f"Max Drawdown: {backtest_results['max_drawdown_percent']:.2f}%")
        logger.info(f"Nombre de trades: {backtest_results['num_trades']}")
        logger.info(f"Trades gagnants: {backtest_results['winning_trades']}")
        logger.info(f"Win Rate: {backtest_results['win_rate']:.1f}%")
    
    # ===== 5. AUTO OPTIMISATION =====
    logger.info("\n" + "="*60)
    logger.info("5️⃣ AUTO OPTIMISATION - optimize_strategy()")
    logger.info("="*60)
    logger.info("Optimisation en cours (peut prendre 30-60 secondes)...")
    optimize_results = analytics.optimize_strategy(data, simple_signal)
    if optimize_results:
        logger.info(f"\nMeilleurs parametres trouves:")
        for key, value in optimize_results['best_params'].items():
            logger.info(f"   {key}: {value}")
        logger.info(f"ROI avec ces parametres: {optimize_results['best_roi']:.2f}%")
        
        logger.info(f"\nTop 5 configurations:")
        for i, result in enumerate(optimize_results['top_results'], 1):
            logger.info(f"   {i}. SMA({result['sma_s']}/{result['sma_l']}) RSI({result['rsi_l']}/{result['rsi_u']}) -> ROI={result['roi']:.2f}%")
    
    logger.info("\n" + "="*60)
    logger.info("TEST TERMINE")
    logger.info("="*60)

if __name__ == "__main__":
    test_advanced_features()
