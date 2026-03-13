"""
Exchange Manager – Multi-exchange integration with CCXT
Supports: Binance, Bybit, Kraken, Coinbase Pro

Usage:
    from core.exchange_manager import ExchangeManager
    from config import CONFIG
    
    mgr = ExchangeManager(CONFIG)
    ticker = await mgr.fetch_ticker("BTC/USDT")
"""

import ccxt
import logging
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)


class ExchangeManager:
    """Unified multi-exchange interface with fallback and error handling"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize exchanges from config"""
        self.config = config
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.primary_exchange = config.get('primary_exchange', 'binance')
        self._initialize_exchanges()

    def _initialize_exchanges(self):
        """Load all configured exchanges"""
        for name, settings in self.config.get('exchanges', {}).items():
            try:
                exchange_class = getattr(ccxt, name.lower())
                self.exchanges[name] = exchange_class({
                    'apiKey': settings.get('apiKey', ''),
                    'secret': settings.get('secret', ''),
                    'enableRateLimit': True,
                    'timeout': 30000,
                })
                logger.info(f"✅ Exchange initialized: {name}")
            except Exception as e:
                logger.error(f"❌ Failed to init {name}: {e}")

    async def fetch_ticker(self, symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
        """Fetch ticker with fallback"""
        target_exchange = exchange or self.primary_exchange
        
        if target_exchange not in self.exchanges:
            logger.warning(f"Exchange {target_exchange} not available, using primary")
            target_exchange = self.primary_exchange

        try:
            ticker = self.exchanges[target_exchange].fetch_ticker(symbol)
            return {'exchange': target_exchange, 'data': ticker, 'status': 'ok'}
        except Exception as e:
            logger.error(f"Fetch failed for {symbol} on {target_exchange}: {e}")
            # Fallback to other exchanges
            for name, exch in self.exchanges.items():
                if name != target_exchange:
                    try:
                        ticker = exch.fetch_ticker(symbol)
                        return {'exchange': name, 'data': ticker, 'status': 'fallback'}
                    except:
                        continue
            return {'exchange': None, 'data': None, 'status': 'failed'}

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Any]:
        """Fetch OHLCV data"""
        try:
            ohlcv = self.exchanges[self.primary_exchange].fetch_ohlcv(
                symbol, timeframe, limit=limit
            )
            return ohlcv
        except Exception as e:
            logger.error(f"OHLCV fetch failed: {e}")
            return []

    def get_supported_symbols(self, exchange: Optional[str] = None) -> List[str]:
        """Get list of supported trading pairs"""
        target = exchange or self.primary_exchange
        try:
            symbols = self.exchanges[target].symbols or []
            return symbols[:50]  # Top 50
        except Exception:
            return []

    async def place_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Place order (market or limit)"""
        try:
            normalized_side: Literal['buy', 'sell'] = 'buy' if side.lower() == 'buy' else 'sell'

            if order_type == 'market':
                order = self.exchanges[self.primary_exchange].create_market_order(
                    symbol, normalized_side, amount
                )
            else:  # limit
                if price is None:
                    raise ValueError("price is required for limit orders")
                order = self.exchanges[self.primary_exchange].create_limit_order(
                    symbol, normalized_side, amount, price
                )
            logger.info(f"✅ Order placed: {side} {amount} {symbol}")
            return order
        except Exception as e:
            logger.error(f"❌ Order failed: {e}")
            return None

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        try:
            self.exchanges[self.primary_exchange].cancel_order(order_id, symbol)
            logger.info(f"✅ Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Cancel failed: {e}")
            return False

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        try:
            balance = self.exchanges[self.primary_exchange].fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"❌ Balance fetch failed: {e}")
            return {}
