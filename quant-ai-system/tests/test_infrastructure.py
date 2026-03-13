"""
Unit tests for infrastructure modules
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from infrastructure.paper_trading import PaperTradingAccount, PaperTradingMode
from infrastructure.risk_limits import RiskLimits, RiskManager
from infrastructure.monitoring import SystemMetrics, MonitoringSystem, Alert


class TestPaperTrading:
    """Tests for paper trading mode"""
    
    def test_account_initialization(self):
        """Test account initialization"""
        account = PaperTradingAccount(initial_balance=100000)
        assert account.initial_balance == 100000
        assert account.balance == 100000
        assert len(account.positions) == 0
        assert len(account.closed_trades) == 0
    
    def test_buy_order(self):
        """Test buy order placement"""
        account = PaperTradingAccount(initial_balance=100000)
        
        # Buy 0.5 BTC at 42000
        result = account.place_buy_order('BTC/USDT', 0.5, 42000)
        
        assert result is True
        assert 'BTC/USDT' in account.positions
        assert account.balance < 100000  # Balance reduced
        assert account.trades_executed == 1
    
    def test_insufficient_balance(self):
        """Test insufficient balance check"""
        account = PaperTradingAccount(initial_balance=10000)
        
        # Try to buy expensive position
        result = account.place_buy_order('BTC/USDT', 10, 42000)
        
        assert result is False
        assert 'BTC/USDT' not in account.positions
    
    def test_sell_order(self):
        """Test sell order placement"""
        account = PaperTradingAccount(initial_balance=100000)
        
        # Buy first
        account.place_buy_order('BTC/USDT', 0.5, 42000)
        initial_trades = account.trades_closed
        
        # Sell
        result = account.place_sell_order('BTC/USDT', 0.5, 43000)
        
        assert result is True
        assert 'BTC/USDT' not in account.positions
        assert account.trades_closed == initial_trades + 1
        assert account.balance > 100000  # Profit
    
    def test_position_update(self):
        """Test position price update"""
        account = PaperTradingAccount(initial_balance=100000)
        account.place_buy_order('BTC/USDT', 1.0, 40000)
        
        # Update price
        account.update_position_prices({'BTC/USDT': 42000})
        
        position = account.positions['BTC/USDT']
        assert position.current_price == 42000
        assert position.pnl == 2000  # 1 * (42000 - 40000)
    
    def test_account_value(self):
        """Test account value calculation"""
        account = PaperTradingAccount(initial_balance=100000)
        account.place_buy_order('BTC/USDT', 1.0, 40000)
        account.update_position_prices({'BTC/USDT': 42000})
        
        value = account.get_account_value()
        # Should be close to initial + 2000 profit
        assert 101900 < value < 102100


class TestRiskManagement:
    """Tests for risk management"""
    
    def test_risk_manager_initialization(self):
        """Test risk manager initialization"""
        limits = RiskLimits(max_position_size_pct=0.1, max_daily_loss_pct=0.05)
        mgr = RiskManager(limits, initial_balance=100000)
        
        assert mgr.current_balance == 100000
        assert mgr.peak_balance == 100000
        assert mgr.is_trading_allowed is True
    
    def test_can_place_trade(self):
        """Test trade approval"""
        limits = RiskLimits(position_size_limit=10000)
        mgr = RiskManager(limits, initial_balance=100000)
        
        trade = {
            'quantity': 1,
            'price': 5000,
            'estimated_loss': 1000
        }
        
        allowed, reason = mgr.can_place_trade(trade)
        assert allowed is True
        assert reason is None
    
    def test_trade_size_limit(self):
        """Test position size limit"""
        limits = RiskLimits(position_size_limit=5000)
        mgr = RiskManager(limits, initial_balance=100000)
        
        trade = {
            'quantity': 2,
            'price': 3000,  # 6000 - exceeds limit
            'estimated_loss': 500
        }
        
        allowed, reason = mgr.can_place_trade(trade)
        assert allowed is False
        assert 'exceeds limit' in reason
    
    def test_daily_loss_limit(self):
        """Test daily loss limit"""
        limits = RiskLimits(max_daily_loss_pct=0.05)
        mgr = RiskManager(limits, initial_balance=100000)
        
        # Simulate 4% daily loss (under limit)
        mgr.update_balance(96000)
        allowed, reason = mgr.can_place_trade({'quantity': 1, 'price': 1000})
        assert allowed is True
        
        # Simulate 6% daily loss (exceeds limit)
        mgr.update_balance(94000)
        allowed, reason = mgr.can_place_trade({'quantity': 1, 'price': 1000})
        assert allowed is False
    
    def test_max_positions_limit(self):
        """Test max positions limit"""
        limits = RiskLimits(max_positions=3)
        mgr = RiskManager(limits, initial_balance=100000)
        
        # Register 3 positions
        mgr.register_position('BTC/USDT', 0.5, 40000)
        mgr.register_position('ETH/USDT', 5.0, 2000)
        mgr.register_position('SOL/USDT', 10.0, 100)
        
        # Try to add 4th - should fail
        trade = {'quantity': 1, 'price':1000}
        allowed, reason = mgr.can_place_trade(trade)
        assert allowed is False
        assert 'Maximum positions' in reason


class TestMonitoring:
    """Tests for monitoring system"""
    
    def test_metrics_recording(self):
        """Test metrics recording"""
        monitoring = MonitoringSystem()
        
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_usage=50.0,
            memory_usage=60.0,
            active_agents=5,
            completed_trades=10
        )
        
        monitoring.record_metrics(metrics)
        
        assert len(monitoring.metrics_history) == 1
        assert monitoring.get_latest_metrics() == metrics
    
    def test_alert_creation(self):
        """Test alert creation"""
        monitoring = MonitoringSystem()
        
        alert = Alert(
            level='WARNING',
            title='Test Alert',
            message='This is a test'
        )
        
        monitoring.create_alert(alert)
        
        assert len(monitoring.alerts) == 1
        assert monitoring.alerts[0].title == 'Test Alert'
    
    def test_threshold_checking(self):
        """Test threshold checking"""
        monitoring = MonitoringSystem()
        
        # High CPU should trigger alert
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_usage=95.0,
            memory_usage=50.0,
            active_agents=5
        )
        
        monitoring.record_metrics(metrics)
        
        # Should have created alert
        assert len(monitoring.alerts) > 0
        assert 'CPU' in monitoring.alerts[0].title
    
    def test_metrics_summary(self):
        """Test metrics summary"""
        monitoring = MonitoringSystem()
        
        for i in range(5):
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=50.0 + i * 5,
                memory_usage=40.0 + i * 5,
                active_agents=5,
                completed_trades=10 + i
            )
            monitoring.record_metrics(metrics)
        
        summary = monitoring.get_metrics_summary(timedelta(hours=1))
        
        assert summary['count'] == 5
        assert summary['avg_cpu'] > 50
        assert summary['total_trades'] > 50


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_paper_trading_flow(self):
        """Test complete paper trading flow"""
        paper = PaperTradingMode(initial_balance=100000)
        
        # Place buy order
        result = await paper.execute_trade({
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'quantity': 0.5,
            'price': 42000
        })
        
        assert result is True
        
        # Check position
        perf = paper.get_performance()
        assert perf['account_summary']['open_positions'] == 1
        assert perf['account_summary']['trades_executed'] == 1
    
    @pytest.mark.asyncio
    async def test_risk_monitoring_flow(self):
        """Test risk monitoring flow"""
        limits = RiskLimits(max_daily_loss_pct=0.1)
        mgr = RiskManager(limits, initial_balance=100000)
        
        # Register position
        mgr.register_position('BTC/USDT', 1.0, 40000)
        
        # Check portfolio risk
        risk = mgr.get_portfolio_risk()
        assert risk['open_positions'] == 1
        assert risk['trading_allowed'] is True
        
        # Simulate loss
        mgr.update_balance(92000)
        
        # Should still allow trading (within limit)
        allowed, _ = mgr.can_place_trade({'quantity': 1, 'price': 1000})
        assert allowed is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
