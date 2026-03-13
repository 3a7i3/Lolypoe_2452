"""
Risk Engine – Advanced risk management with drawdown tracking
VaR, max drawdown, circuit breakers, kill-switch
"""

import numpy as np
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class RiskEngine:
    """Manage system risk and portfolio safety"""

    def __init__(self, max_drawdown: float = 0.20, var_confidence: float = 0.95):
        """Initialize risk engine"""
        self.max_drawdown = max_drawdown
        self.var_confidence = var_confidence
        self.peak_value = 0
        self.current_value = 0
        self.equity_curve = []
        self.status = "OK"

    def update_equity(self, current_value: float):
        """Track equity curve"""
        self.current_value = current_value
        self.equity_curve.append(current_value)
        
        if current_value > self.peak_value:
            self.peak_value = current_value

    def calculate_drawdown(self) -> float:
        """Calculate current drawdown percentage"""
        if self.peak_value == 0:
            return 0
        return ((self.current_value - self.peak_value) / self.peak_value)

    def calculate_var(self, returns: np.ndarray) -> float:
        """Calculate Value at Risk (VaR)"""
        if len(returns) == 0:
            return 0
        return np.percentile(returns, (1 - self.var_confidence) * 100)

    def calculate_max_drawdown_historical(self) -> float:
        """Calculate max drawdown from history"""
        if len(self.equity_curve) == 0:
            return 0
        
        peak = self.equity_curve[0]
        max_dd = 0
        
        for value in self.equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        return max_dd

    def check_risk_limits(self) -> Dict[str, Any]:
        """Check if risk limits are violated"""
        current_dd = self.calculate_drawdown()
        max_dd = self.calculate_max_drawdown_historical()
        
        violations = []
        
        if current_dd < self.max_drawdown:
            self.status = "OK"
        elif current_dd < self.max_drawdown * 1.1:
            self.status = "WARNING"
            violations.append(f"Drawdown warning: {current_dd:.2%}")
        else:
            self.status = "CRITICAL"
            violations.append(f"DRAWDOWN EXCEEDED: {current_dd:.2%} > {self.max_drawdown:.2%}")

        return {
            'status': self.status,
            'current_drawdown': current_dd,
            'max_drawdown': max_dd,
            'violations': violations,
            'should_stop': len(violations) > 0 and self.status == "CRITICAL"
        }

    def should_kill_switch(self) -> bool:
        """Determine if system should stop trading"""
        risk_check = self.check_risk_limits()
        return risk_check['should_stop']

    def risk_report(self) -> Dict[str, Any]:
        """Generate full risk report"""
        current_dd = self.calculate_drawdown()
        max_dd = self.calculate_max_drawdown_historical()
        
        if len(self.equity_curve) > 1:
            returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])
            sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            var = self.calculate_var(returns)
        else:
            sharpe = 0
            var = 0

        return {
            'portfolio_value': self.current_value,
            'peak_value': self.peak_value,
            'current_drawdown': current_dd,
            'max_drawdown': max_dd,
            'sharpe_ratio': sharpe,
            'var_95': var,
            'status': self.status,
            'alert_level': 'CRITICAL' if self.status == 'CRITICAL' else 'OK'
        }
