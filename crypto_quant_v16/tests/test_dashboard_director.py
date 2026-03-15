import unittest
from crypto_quant_v16.supervision.dashboard_director import DashboardDirector

class TestDashboardDirector(unittest.TestCase):
    def setUp(self):
        self.dashboard = DashboardDirector()

    def test_update_strategies_status(self):
        strategies = [{"strategy": "momentum", "pnl": 1.2, "status": "active"}]
        self.dashboard.update_strategies_status(strategies)
        self.assertEqual(self.dashboard.strategies_status, strategies)

    def test_update_portfolio(self):
        summary = {"total_capital": 10000, "total_allocated": 9500, "num_strategies": 3}
        self.dashboard.update_portfolio(summary)
        self.assertEqual(self.dashboard.portfolio_summary, summary)

    def test_log_trades(self):
        trades = [{"token": "TOKEN_1", "status": "executed_simulated"}]
        self.dashboard.log_trades(trades)
        self.assertIn(trades[0], self.dashboard.trades_log)

    def test_add_alert(self):
        self.dashboard.add_alert("Test alert")
        self.assertIn("Test alert", self.dashboard.alerts)

if __name__ == '__main__':
    unittest.main()
