"""
Live Monitor - Monitoring en temps reel
"""

from datetime import datetime
from utils.logger import logger

class LiveMonitor:
    """Monitor en temps reel du bot."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'last_signal': None,
            'last_signal_time': None
        }
    
    def update_metrics(self, trade_data):
        """Met a jour les metriques."""
        if trade_data.get('signal') in ['BUY', 'SELL']:
            self.metrics['total_trades'] += 1
            self.metrics['last_signal'] = trade_data.get('signal')
            self.metrics['last_signal_time'] = datetime.now()
        
        if trade_data.get('pnl', 0) > 0:
            self.metrics['winning_trades'] += 1
        elif trade_data.get('pnl', 0) < 0:
            self.metrics['losing_trades'] += 1
        
        self.metrics['total_pnl'] += trade_data.get('pnl', 0)
        self.last_update = datetime.now()
    
    def get_status(self):
        """Retourne le status actuel."""
        uptime = datetime.now() - self.start_time
        
        win_rate = (self.metrics['winning_trades'] / self.metrics['total_trades'] * 100) \
                   if self.metrics['total_trades'] > 0 else 0
        
        return {
            'uptime': str(uptime),
            'total_trades': self.metrics['total_trades'],
            'win_rate': f"{win_rate:.1f}%",
            'total_pnl': f"${self.metrics['total_pnl']:.2f}",
            'last_signal': self.metrics['last_signal'],
            'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def print_status(self):
        """Affiche le status."""
        status = self.get_status()
        logger.info(f"[MONITOR] Uptime: {status['uptime']}, Trades: {status['total_trades']}, "
                   f"Win Rate: {status['win_rate']}, PnL: {status['total_pnl']}")
