"""
Risk Engine - Gestion avancee du risque
"""

import numpy as np
from config import MAX_DRAWDOWN_PERCENT, DAILY_LOSS_LIMIT, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT
from config import TRAILING_STOP_PERCENT
from utils.logger import logger, log_risk_event

class RiskEngine:
    """Gere les risques du portefeuille."""
    
    def __init__(self, initial_capital):
        self.initial_capital = initial_capital
        self.peak_value = initial_capital
        self.daily_pnl = 0
        self.active_positions = {}  # {symbol: {'entry_price': X, 'stop_loss': Y, 'take_profit': Z}}
    
    def check_risk_limits(self, portfolio_value, daily_pnl):
        """Verifie les limites de risque."""
        # Max drawdown
        max_drawdown = ((self.peak_value - portfolio_value) / self.peak_value)
        if max_drawdown > MAX_DRAWDOWN_PERCENT:
            log_risk_event("MAX_DRAWDOWN", f"Drawdown: {max_drawdown:.2%}")
            return False
        
        # Daily loss limit
        if daily_pnl < -self.initial_capital * DAILY_LOSS_LIMIT:
            log_risk_event("DAILY_LOSS_LIMIT", f"Daily loss: {daily_pnl:.2f}")
            return False
        
        return True
    
    def update_peak_value(self, current_value):
        """Met a jour le pic de valeur."""
        if current_value > self.peak_value:
            self.peak_value = current_value
    
    def calculate_position_size(self, capital, stop_loss_price, entry_price, risk_amount):
        """Calcule la taille de position."""
        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit == 0:
            return 0
        
        position_size = risk_amount / risk_per_unit
        return position_size
    
    def set_stop_loss_and_take_profit(self, symbol, entry_price):
        """Defini les niveaux SL et TP."""
        stop_loss = entry_price * (1 - STOP_LOSS_PERCENT)
        take_profit = entry_price * (1 + TAKE_PROFIT_PERCENT)
        
        self.active_positions[symbol] = {
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'highest_price': entry_price
        }
        
        return stop_loss, take_profit
    
    def update_trailing_stop(self, symbol, current_price):
        """Met a jour le trailing stop."""
        if symbol not in self.active_positions:
            return False
        
        position = self.active_positions[symbol]
        
        # Si nouveau high, relever le stop
        if current_price > position['highest_price']:
            position['highest_price'] = current_price
            new_stop = current_price * (1 - TRAILING_STOP_PERCENT)
            position['stop_loss'] = max(position['stop_loss'], new_stop)
        
        # Checker si stop est atteint
        if current_price <= position['stop_loss']:
            logger.warning(f"TRAILING STOP HIT: {symbol} @ {current_price:.2f}")
            return True
        
        return False
    
    def check_take_profit(self, symbol, current_price):
        """Verifie si le TP est atteint."""
        if symbol not in self.active_positions:
            return False
        
        position = self.active_positions[symbol]
        if current_price >= position['take_profit']:
            logger.info(f"TAKE PROFIT HIT: {symbol} @ {current_price:.2f}")
            return True
        
        return False
    
    def calculate_value_at_risk(self, portfolio_value, confidence_level=0.95):
        """Calcule le Value at Risk."""
        # VaR simplified
        daily_return_std = 0.02  # Assume 2% daily std
        z_score = 1.645  # Pour 95%
        var = portfolio_value * daily_return_std * z_score
        return var
    
    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.02):
        """Calcule le Sharpe Ratio."""
        if len(returns) == 0:
            return 0
        
        excess_returns = np.mean(returns) - risk_free_rate
        std_dev = np.std(returns)
        
        if std_dev == 0:
            return 0
        
        sharpe = (excess_returns / std_dev) * np.sqrt(252)  # Annualize
        return sharpe
    
    def calculate_sortino_ratio(self, returns, risk_free_rate=0.02):
        """Calcule le Sortino Ratio."""
        if len(returns) == 0:
            return 0
        
        excess_returns = np.mean(returns) - risk_free_rate
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            downside_std = 0
        else:
            downside_std = np.std(downside_returns)
        
        if downside_std == 0:
            return 0
        
        sortino = (excess_returns / downside_std) * np.sqrt(252)
        return sortino
