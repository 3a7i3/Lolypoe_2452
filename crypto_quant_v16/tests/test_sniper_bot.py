import unittest
import asyncio
from memecoin_alpha.sniper_bot import SniperBot

class DummyExecutionEngine:
    async def create_order(self, symbol, side, amount, price=None, order_type='market'):
        return {'id': 1, 'symbol': symbol, 'side': side, 'amount': amount, 'price': price, 'type': order_type, 'status': 'closed'}

class TestSniperBot(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = DummyExecutionEngine()
        self.bot = SniperBot(self.engine, mode='paper', slippage_pct=0.01, fees_pct=0.001)

    async def test_snipe_trade_log(self):
        await self.bot.snipe('TOKEN1', 1000)
        log = self.bot.get_trade_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]['symbol'], 'TOKEN1')
        self.assertAlmostEqual(log[0]['amount'], 999.0, places=1)

    async def test_failed_trade(self):
        class FailingEngine:
            async def create_order(self, *a, **kw):
                return None
        bot = SniperBot(FailingEngine(), mode='paper')
        await bot.snipe('TOKEN2', 1000)
        self.assertEqual(len(bot.get_trade_log()), 0)

if __name__ == '__main__':
    unittest.main()
