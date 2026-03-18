"""
Sniper Bot – Fast-entry trading with risk controls
"""

import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SniperBot:
    """
    SniperBot for fast-entry trading on new tokens with risk management.
    Supports paper/live mode, slippage, and fees configuration.
    """
    def __init__(self, execution_engine, mode: str = None, slippage_pct: float = None, fees_pct: float = None):
        self.execution_engine = execution_engine
        self.mode = mode or os.environ.get("SNIPER_MODE", "paper")
        self.slippage_pct = float(slippage_pct if slippage_pct is not None else os.environ.get("SNIPER_SLIPPAGE_PCT", 0.005))
        self.fees_pct = float(fees_pct if fees_pct is not None else os.environ.get("SNIPER_FEES_PCT", 0.001))
        self.trade_log = []

    async def snipe(self, symbol: str, amount: float):
        """
        Execute a fast-entry trade with slippage and fees applied.
        """
        # Simulate slippage
        price = await self.get_market_price(symbol)
        price_with_slippage = price * (1 + self.slippage_pct)
        logger.info(f"Snipe {symbol}: price={price}, slippage={self.slippage_pct*100:.2f}%, final={price_with_slippage}")
        # Place order
        order = await self.execution_engine.create_order(symbol, 'buy', amount, price=price_with_slippage)
        if order:
            # Apply fees
            net_amount = amount * (1 - self.fees_pct)
            self.trade_log.append({"symbol": symbol, "amount": net_amount, "order": order})
            logger.info(f"Trade executed: {symbol} net={net_amount}")
        else:
            logger.warning(f"Trade failed for {symbol}")

    async def get_market_price(self, symbol: str) -> float:
        """
        Fetch the current market price (stub for integration).
        """
        # TODO: Integrate with real price feed
        return 1.0

    def get_trade_log(self):
        return self.trade_log
