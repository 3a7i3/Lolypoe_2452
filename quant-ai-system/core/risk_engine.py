"""
Risk Engine
Comprehensive risk management system
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class RiskMetrics:
    """Risk metrics for portfolio"""
    max_drawdown: float
    drawdown_recovery_pct: float
    portfolio_volatility: float
    value_at_risk: float  # VaR 95%
    sharpe_ratio: float
    sortino_ratio: float
    max_single_position_risk: float


class RiskEngine:
    """Manages portfolio risk"""
    
    def __init__(self, max_drawdown: float = 0.25, max_daily_loss: float = 0.05,
                 max_position_risk: float = 0.02, stop_loss_percent: float = 0.10):
        """
        Initialize risk engine
        Args:
            max_drawdown: Maximum acceptable drawdown (25%)
            max_daily_loss: Maximum daily loss (5%)
            max_position_risk: Max risk per position (2%)
            stop_loss_percent: Automatic stop loss at X% loss
        """
        self.max_drawdown = max_drawdown
        self.max_daily_loss = max_daily_loss
        self.max_position_risk = max_position_risk
        self.stop_loss_percent = stop_loss_percent
        
        self.equity_curve = []
        self.position_stops = {}  # Symbol -> stop price
        self.alerts = []
        self.risk_violations = []
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> Tuple[float, int]:
        """Calculate maximum drawdown and its duration
        Returns: (max_drawdown, duration_bars)
        """
        if len(equity_curve) < 2:
            return 0, 0
        
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        
        max_dd_idx = np.argmin(equity_array / running_max)
        max_dd = drawdown[max_dd_idx]
        
        # Find recovery
        dd_value = equity_array[max_dd_idx]
        recovery_idx = np.where(equity_array[max_dd_idx:] >= running_max[max_dd_idx])[0]
        duration = recovery_idx[0] if len(recovery_idx) > 0 else len(equity_curve) - max_dd_idx
        
        return max_dd, duration
    
    def calculate_var(self, returns: List[float], confidence: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)"""
        if len(returns) < 10:
            return 0
        
        returns_array = np.array(returns)
        var = np.percentile(returns_array, (1 - confidence) * 100)
        
        return var
    
    def calculate_volatility(self, equity_curve: List[float]) -> float:
        """Calculate portfolio volatility (annualized)"""
        if len(equity_curve) < 2:
            return 0
        
        returns = np.diff(equity_curve) / equity_curve[:-1]
        daily_vol = np.std(returns)
        annualized_vol = daily_vol * np.sqrt(252)
        
        return annualized_vol
    
    def calculate_sharpe_ratio(self, returns: List[float], rf_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - rf_rate / 252
        
        if np.std(excess_returns) == 0:
            return 0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        return sharpe
    
    def calculate_sortino_ratio(self, returns: List[float], rf_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside deviation only)"""
        if len(returns) < 2:
            return 0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - rf_rate / 252
        
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return 0
        
        downside_dev = np.std(downside_returns)
        
        if downside_dev == 0:
            return 0
        
        sortino = np.mean(excess_returns) / downside_dev * np.sqrt(252)
        
        return sortino
    
    def check_daily_loss_limit(self, daily_pnl: float, portfolio_value: float) -> bool:
        """Check if daily loss exceeded"""
        daily_loss_pct = abs(daily_pnl) / portfolio_value
        
        if daily_loss_pct > self.max_daily_loss and daily_pnl < 0:
            self.risk_violations.append({
                'type': 'DAILY_LOSS_LIMIT',
                'value': daily_loss_pct,
                'limit': self.max_daily_loss
            })
            return False
        
        return True
    
    def check_drawdown_limit(self, equity_curve: List[float]) -> bool:
        """Check if maximum drawdown exceeded"""
        max_dd, _ = self.calculate_max_drawdown(equity_curve)
        
        if max_dd < -self.max_drawdown:
            self.risk_violations.append({
                'type': 'DRAWDOWN_LIMIT',
                'value': max_dd,
                'limit': -self.max_drawdown
            })
            return False
        
        return True
    
    def calculate_position_stops(self, positions: Dict[str, Any]) -> Dict[str, float]:
        """Calculate stop loss prices for all positions"""
        stops = {}
        
        for symbol, position in positions.items():
            stop_price = position['entry_price'] * (1 - self.stop_loss_percent)
            stops[symbol] = stop_price
        
        self.position_stops = stops
        return stops
    
    def check_position_stops(self, current_prices: Dict[str, float]) -> List[str]:
        """Check if any positions hit stop loss
        Returns: List of symbols to close
        """
        to_close = []
        
        for symbol, stop_price in self.position_stops.items():
            if symbol in current_prices:
                if current_prices[symbol] <= stop_price:
                    to_close.append(symbol)
                    self.alerts.append({
                        'type': 'STOP_LOSS_HIT',
                        'symbol': symbol,
                        'price': current_prices[symbol],
                        'stop': stop_price
                    })
        
        return to_close
    
    def get_risk_metrics(self, portfolio_value: float, equity_curve: List[float],
                        returns: List[float]) -> RiskMetrics:
        """Get complete risk metrics"""
        max_dd, _ = self.calculate_max_drawdown(equity_curve)
        
        # Recovery percentage
        if len(equity_curve) > 0:
            peak = max(equity_curve)
            recovery_pct = (portfolio_value - (peak + max_dd * peak)) / (peak * abs(max_dd))
            recovery_pct = np.clip(recovery_pct, 0, 1)
        else:
            recovery_pct = 0
        
        vol = self.calculate_volatility(equity_curve)
        var = self.calculate_var(returns)
        sharpe = self.calculate_sharpe_ratio(returns)
        sortino = self.calculate_sortino_ratio(returns)
        
        return RiskMetrics(
            max_drawdown=max_dd,
            drawdown_recovery_pct=recovery_pct,
            portfolio_volatility=vol,
            value_at_risk=var,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_single_position_risk=self.max_position_risk
        )
    
    def add_alert(self, alert_type: str, message: str, severity: str = 'INFO'):
        """Add risk alert"""
        self.alerts.append({
            'type': alert_type,
            'message': message,
            'severity': severity
        })
    
    def get_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alerts[-limit:]
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []


# Convenience functions
_risk_engine = None


def initialize_risk_engine(max_drawdown: float = 0.25) -> RiskEngine:
    """Initialize risk engine"""
    global _risk_engine
    _risk_engine = RiskEngine(max_drawdown=max_drawdown)
    return _risk_engine


def get_risk_engine() -> RiskEngine:
    """Get risk engine instance"""
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine
