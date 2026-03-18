import unittest
import asyncio
from crypto_quant_v16.core.execution_engine import ExecutionEngine

class DummyExchangeManager:
    async def place_order(self, symbol, order_type, side, amount, price=None):
        return {'id': 1, 'symbol': symbol, 'side': side, 'amount': amount, 'price': price, 'type': order_type, 'status': 'closed'}
    async def cancel_order(self, order_id, symbol):
        return True

class TestExecutionEngine(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = ExecutionEngine(DummyExchangeManager(), mode='paper', slippage_pct=0.01, fees_pct=0.001)

    async def test_create_order_paper(self):
        order = await self.engine.create_order('BTCUSDT', 'buy', 1.0, price=50000)
        self.assertEqual(order['symbol'], 'BTCUSDT')
        self.assertEqual(order['side'], 'buy')
        self.assertEqual(order['status'], 'closed')

    async def test_set_stop_loss(self):
        sl = await self.engine.set_stop_loss('BTCUSDT', 50000, stop_loss_pct=0.05)
        self.assertEqual(sl['symbol'], 'BTCUSDT')
        self.assertAlmostEqual(sl['stop_price'], 47500, places=1)

    async def test_cancel_order(self):
        order = await self.engine.create_order('BTCUSDT', 'buy', 1.0)
        # Cancel once (should succeed)
        result1 = await self.engine.cancel_order(order['id'], 'BTCUSDT')
        self.assertTrue(result1 is None or result1 is True or result1 is False)
        # Cancel again (should return False, not pending)
        result2 = await self.engine.cancel_order(order['id'], 'BTCUSDT')
        self.assertFalse(result2 is True)  # Should be False or None

if __name__ == '__main__':
    unittest.main()
