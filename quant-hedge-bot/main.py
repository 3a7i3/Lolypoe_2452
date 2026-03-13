"""
Main Orchestrator - Quant Hedge Bot
====================================
Chef d'orchestre du bot de trading quantitatif hedge fund
"""

import time
from datetime import datetime
from config import SYMBOLS, SCHEDULE_ENABLED, RUN_INTERVAL_MINUTES, DEBUG_MODE

# Core modules
from core.market_scanner import scan_market, get_top_gainers, get_top_losers
from core.data_pipeline import DataPipeline
from core.indicators_engine import IndicatorsEngine
from core.strategy_engine import StrategyEngine
from core.ai_predictor import AIPredictor
from core.portfolio_manager import PortfolioManager
from core.risk_engine import RiskEngine
from core.trade_executor import TradeExecutor

# Quant modules
from quant.backtester import Backtester
from quant.regime_detection import RegimeDetector
from quant.anomaly_detection import AnomalyDetector
from quant.feature_engineering import FeatureEngineering

# Dashboard
from dashboard.live_monitor import LiveMonitor

# Utils
from utils.logger import logger
from utils.database import db

class QuantHedgeBot:
    """Bot de trading quantitatif hedge fund."""
    
    def __init__(self):
        logger.info("="*60)
        logger.info("QUANT HEDGE BOT - Initialization")
        logger.info("="*60)
        
        # Initialize components
        self.portfolio = PortfolioManager()
        self.risk_engine = RiskEngine(self.portfolio.capital)
        self.executor = TradeExecutor()
        self.predictor = AIPredictor()
        self.monitor = LiveMonitor()
        
        self.market_data = {}
        self.signals = {}
        self.regime = 'UNKNOWN'
        self.anomalies = []
        
        logger.info("Bot initialized successfully")
    
    def scan_and_prepare_data(self):
        """Scanne le marche et prepare les donnees."""
        logger.info("[STEP 1] Scanning market...")
        
        self.market_data = scan_market()
        
        if not self.market_data:
            logger.warning("No market data available")
            return False
        
        logger.info(f"Market scan complete: {len(self.market_data)} symbols")
        
        # Show top gainers/losers
        gainers = get_top_gainers(self.market_data, 3)
        losers = get_top_losers(self.market_data, 3)
        
        logger.info(f"Top Gainers: {[(g['symbol'], f\"{g['price_change']:.2f}%\") for g in gainers]}")
        logger.info(f"Top Losers: {[(l['symbol'], f\"{l['price_change']:.2f}%\") for l in losers]}")
        
        return True
    
    def process_data_and_indicators(self):
        """Traite les donnees et calcule les indicateurs."""
        logger.info("[STEP 2] Processing data and calculating indicators...")
        
        for symbol, data in self.market_data.items():
            try:
                # Clean data
                data = DataPipeline.clean_data(data)
                if data is None:
                    continue
                
                # Add features
                data = DataPipeline.add_features(data)
                
                # Add all indicators
                data = IndicatorsEngine.add_all_indicators(data)
                
                # Update market data
                self.market_data[symbol] = data
                
                logger.debug(f"{symbol}: {len(data)} bars processed")
            
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        logger.info("Data processing complete")
    
    def detect_regime_and_anomalies(self):
        """Detecte le regime et les anomalies."""
        logger.info("[STEP 3] Detecting market regime and anomalies...")
        
        if not self.market_data:
            return
        
        # Use first symbol's data for market regime
        first_symbol = list(self.market_data.keys())[0]
        data = self.market_data[first_symbol]
        
        self.regime = RegimeDetector.detect_regime(data)
        confidence = RegimeDetector.get_regime_confidence(data)
        logger.info(f"Market Regime: {self.regime} (Confidence: {confidence:.1%})")
        
        # Detect anomalies
        for symbol, data in self.market_data.items():
            anomalies = AnomalyDetector.detect_anomalies(data)
            if anomalies:
                self.anomalies.extend([(symbol, a) for a in anomalies])
    
    def generate_signals(self):
        """Genere les signaux de trading."""
        logger.info("[STEP 4] Generating trading signals...")
        
        self.signals = {}
        
        for symbol, data in self.market_data.items():
            try:
                # Get signal with confidence
                signal_data = StrategyEngine.generate_signal_with_confidence(data)
                
                self.signals[symbol] = signal_data['signal']
                
                # Log signals with confidence > 0.6
                if signal_data['confidence'] > 0.6 and signal_data['signal'] != 'HOLD':
                    logger.info(f"{symbol} {signal_data['signal']} (Confidence: {signal_data['confidence']:.1%})")
            
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                self.signals[symbol] = 'HOLD'
        
        logger.info(f"Signals generated: {sum(1 for s in self.signals.values() if s != 'HOLD')} active signals")
    
    def manage_portfolio(self):
        """Gere le portefeuille."""
        logger.info("[STEP 5] Managing portfolio...")
        
        # Calculate portfolio weights
        weights = self.portfolio.calculate_portfolio_weights(self.market_data, self.signals)
        
        # Allocate capital
        allocations = self.portfolio.allocate_capital(weights)
        
        # Log allocation
        for symbol, allocation in allocations.items():
            if allocation > 0:
                logger.info(f"{symbol}: ${allocation:.2f} ({allocation/self.portfolio.capital*100:.1f}%)")
    
    def execute_trades(self):
        """Execute les trades."""
        logger.info("[STEP 6] Executing trades...")
        
        for symbol, signal in self.signals.items():
            if signal in ['BUY', 'SELL'] and symbol in self.market_data:
                try:
                    data = self.market_data[symbol]
                    current_price = data['Close'].iloc[-1]
                    
                    # Risk check
                    if not self.risk_engine.check_risk_limits(
                        self.portfolio.get_total_portfolio_value(),
                        0
                    ):
                        logger.warning("Risk limits exceeded - stopping trades")
                        break
                    
                    # Set SL/TP
                    stop_loss, take_profit = self.risk_engine.set_stop_loss_and_take_profit(
                        symbol, current_price
                    )
                    
                    # Execute trade
                    result = self.executor.execute_trade(
                        symbol, signal, current_price, 1,
                        reason=f"Regime: {self.regime}"
                    )
                    
                    if result:
                        # Update portfolio
                        quantity = 1  # Simplified
                        self.portfolio.update_position(symbol, quantity, current_price, current_price)
                        
                        # Update monitor
                        self.monitor.update_metrics({'signal': signal, 'pnl': 0})
                
                except Exception as e:
                    logger.error(f"Error executing trade for {symbol}: {e}")
    
    def update_positions_and_risk(self):
        """Update positions et gere les risques."""
        logger.info("[STEP 7] Updating positions and risk management...")
        
        for symbol, data in self.market_data.items():
            if symbol in self.portfolio.positions:
                current_price = data['Close'].iloc[-1]
                
                # Update trailing stop
                should_close = self.risk_engine.update_trailing_stop(symbol, current_price)
                if should_close:
                    logger.warning(f"Trailing stop triggered for {symbol}")
                
                # Check take profit
                should_tp = self.risk_engine.check_take_profit(symbol, current_price)
                if should_tp:
                    logger.info(f"Take profit triggered for {symbol}")
                
                # Update position
                pos = self.portfolio.positions[symbol]
                pnl_percent = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
                self.portfolio.update_position(symbol, pos['quantity'], pos['entry_price'], current_price)
    
    def log_performance(self):
        """Enregistre la performance."""
        logger.info("[STEP 8] Logging performance...")
        
        stats = self.portfolio.get_portfolio_stats()
        
        logger.info(f"Portfolio Value: ${stats['total_value']:.2f}")
        logger.info(f"Total PnL: ${stats['total_pnl']:.2f} ({stats['total_pnl_percent']:.2f}%)")
        logger.info(f"Active Positions: {stats['num_positions']}")
        
        # Print monitor status
        self.monitor.print_status()
    
    def run_cycle(self):
        """Execute un cycle complet du bot."""
        logger.info("\n" + "="*60)
        logger.info(f"BOT CYCLE - {datetime.now()}")
        logger.info("="*60 + "\n")
        
        try:
            # 1. Scan market
            if not self.scan_and_prepare_data():
                return
            
            # 2. Process data
            self.process_data_and_indicators()
            
            # 3. Detect regime
            self.detect_regime_and_anomalies()
            
            # 4. Generate signals
            self.generate_signals()
            
            # 5. Manage portfolio
            self.manage_portfolio()
            
            # 6. Execute trades
            self.execute_trades()
            
            # 7. Update positions
            self.update_positions_and_risk()
            
            # 8. Log performance
            self.log_performance()
            
            logger.info("Cycle complete\n")
        
        except Exception as e:
            logger.error(f"Error in bot cycle: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def run_continuous(self):
        """Execute le bot en boucle continue."""
        logger.info("Starting continuous run...")
        
        try:
            while True:
                self.run_cycle()
                
                # Sleep before next cycle
                sleep_time = RUN_INTERVAL_MINUTES * 60
                logger.info(f"Sleeping for {RUN_INTERVAL_MINUTES} minutes...")
                time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        
        except Exception as e:
            logger.error(f"Fatal error: {e}")

def main():
    """Fonction principale."""
    logger.info("Starting Quant Hedge Bot...")
    
    bot = QuantHedgeBot()
    
    if SCHEDULE_ENABLED:
        bot.run_continuous()
    else:
        bot.run_cycle()

if __name__ == "__main__":
    main()
