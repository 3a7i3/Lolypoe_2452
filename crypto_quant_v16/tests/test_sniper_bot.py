import unittest
from crypto_quant_v16.memecoin_alpha.sniper_bot import SniperBot

class TestSniperBot(unittest.TestCase):
    def setUp(self):
        self.bot = SniperBot(mode="paper")

    def test_buy_token_low_risk(self):
        trade = self.bot.buy_token('TOKEN_1', 1000, 1, 0.8, 'low')
        self.assertEqual(trade['status'], 'executed_simulated')
        self.assertEqual(trade['token'], 'TOKEN_1')

    def test_buy_token_high_risk(self):
        trade = self.bot.buy_token('TOKEN_2', 1000, 1, 0.8, 'high')
        self.assertEqual(trade['status'], 'skipped_high_risk')

    def test_execute_token_report(self):
        report = {
            'TOKEN_1': {'hype_score_social': 0.9, 'rug_risk': 'low'},
            'TOKEN_2': {'hype_score_social': 0.2, 'rug_risk': 'high'}
        }
        trades = self.bot.execute_token_report(report, capital_per_token=500, current_price=2)
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]['status'], 'executed_simulated')
        self.assertEqual(trades[1]['status'], 'skipped_high_risk')

    def test_trade_log(self):
        self.bot.buy_token('TOKEN_3', 100, 1, 0.5, 'low')
        log = self.bot.get_trade_log()
        self.assertTrue(isinstance(log, list))
        self.assertGreaterEqual(len(log), 1)

if __name__ == '__main__':
    unittest.main()
