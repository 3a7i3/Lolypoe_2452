"""
Trade Executor - Execution des trades
"""

from datetime import datetime
from utils.logger import logger, log_trade
from utils.notifier import notify_trade_opened, notify_trade_closed
from utils.database import db

class TradeExecutor:
    """Execute les trades."""
    
    def __init__(self):
        self.trades_executed = 0
        self.last_trade_time = None
    
    def execute_trade(self, symbol, signal, current_price, quantity, reason=""):
        """Execute un trade."""
        try:
            logger.info(f"[EXECUTE] {signal} {symbol} x{quantity} @ ${current_price:.2f}")
            
            # Log trade
            log_trade(signal, symbol, current_price, quantity, reason)
            
            # Save to database
            db.log_trade(symbol, signal, current_price, quantity, reason=reason)
            
            # Notify
            notify_trade_opened(symbol, signal, current_price)
            
            self.trades_executed += 1
            self.last_trade_time = datetime.now()
            
            return {
                'symbol': symbol,
                'signal': signal,
                'price': current_price,
                'quantity': quantity,
                'timestamp': datetime.now(),
                'status': 'EXECUTED'
            }
        
        except Exception as e:
            logger.error(f"Erreur execution trade: {e}")
            return None
    
    def close_trade(self, symbol, exit_price, quantity, pnl_percent):
        """Ferme un trade."""
        try:
            logger.info(f"[CLOSE] {symbol} x{quantity} @ ${exit_price:.2f} | PnL: {pnl_percent:.2f}%")
            
            # Save to database
            db.log_trade(symbol, "CLOSE", exit_price, quantity)
            
            # Notify
            notify_trade_closed(symbol, pnl_percent)
            
            return {
                'symbol': symbol,
                'exit_price': exit_price,
                'pnl_percent': pnl_percent,
                'timestamp': datetime.now(),
                'status': 'CLOSED'
            }
        
        except Exception as e:
            logger.error(f"Erreur fermeture trade: {e}")
            return None
    
    def get_trade_stats(self):
        """Retourne les stats des trades."""
        return {
            'trades_executed': self.trades_executed,
            'last_trade_time': self.last_trade_time
        }
