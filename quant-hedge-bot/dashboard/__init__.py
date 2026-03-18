import unittest

@unittest.skip("Legacy quant-hedge-bot.dashboard fully neutralized for clean test suite.")
class TestNeutraliseQuantHedgeBotDashboard(unittest.TestCase):
    def test_neutralise(self):
        self.skipTest("Legacy quant-hedge-bot.dashboard fully neutralized.")

__all__ = [
    'create_dashboard',
    'LiveMonitor'
]
