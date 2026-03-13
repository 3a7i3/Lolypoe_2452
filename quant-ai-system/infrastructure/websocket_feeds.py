"""
WebSocket Real-Time Market Data Feeds
Live price streams from multiple exchanges
"""

import asyncio
import json
import logging
from typing import Dict, List, Callable, Any, Optional
import websockets
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TradeEvent:
    """Real-time trade event"""
    exchange: str
    symbol: str
    price: float
    quantity: float
    side: str  # 'buy' or 'sell'
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PriceUpdate:
    """Real-time price update"""
    exchange: str
    symbol: str
    bid: float
    ask: float
    bid_size: float
    ask_size: float
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


class WebSocketFeed:
    """Base WebSocket feed handler"""
    
    def __init__(self, exchange: str):
        self.exchange = exchange
        self.is_connected = False
        self.ws = None
        self.callbacks: Dict[str, List[Callable]] = {
            'trade': [],
            'price': [],
            'error': [],
        }
    
    def on_trade(self, callback: Callable):
        """Register trade event callback"""
        self.callbacks['trade'].append(callback)
    
    def on_price(self, callback: Callable):
        """Register price update callback"""
        self.callbacks['price'].append(callback)
    
    def on_error(self, callback: Callable):
        """Register error callback"""
        self.callbacks['error'].append(callback)
    
    async def _emit_trade(self, event: TradeEvent):
        """Emit trade event to callbacks"""
        for callback in self.callbacks['trade']:
            try:
                await callback(event) if asyncio.iscoroutinefunction(callback) else callback(event)
            except Exception as e:
                logger.error(f"Error in trade callback: {e}")
    
    async def _emit_price(self, update: PriceUpdate):
        """Emit price update to callbacks"""
        for callback in self.callbacks['price']:
            try:
                await callback(update) if asyncio.iscoroutinefunction(callback) else callback(update)
            except Exception as e:
                logger.error(f"Error in price callback: {e}")
    
    async def _emit_error(self, error: Exception):
        """Emit error to callbacks"""
        for callback in self.callbacks['error']:
            try:
                await callback(error) if asyncio.iscoroutinefunction(callback) else callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")


class BinanceWebSocketFeed(WebSocketFeed):
    """Binance WebSocket feed"""
    
    def __init__(self):
        super().__init__('binance')
        self.base_url = "wss://stream.binance.com:9443/ws"
    
    async def connect_trades(self, symbol: str):
        """Connect to Binance trade stream"""
        stream_name = f"{symbol.lower().replace('/', '')}@trade"
        url = f"{self.base_url}/{stream_name}"
        
        logger.info(f"Connecting to Binance trade stream: {symbol}")
        
        try:
            async with websockets.connect(url) as ws:
                self.ws = ws
                self.is_connected = True
                logger.info(f"✅ Connected to Binance {symbol} trades")
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        event = TradeEvent(
                            exchange='binance',
                            symbol=symbol,
                            price=float(data['p']),
                            quantity=float(data['q']),
                            side='buy' if data['m'] else 'sell',
                            timestamp=datetime.fromtimestamp(data['T'] / 1000)
                        )
                        await self._emit_trade(event)
                    except Exception as e:
                        logger.error(f"Error parsing trade data: {e}")
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            await self._emit_error(e)
    
    async def connect_ticker(self, symbol: str):
        """Connect to Binance ticker stream"""
        stream_name = f"{symbol.lower().replace('/', '')}@bookTicker"
        url = f"{self.base_url}/{stream_name}"
        
        logger.info(f"Connecting to Binance ticker stream: {symbol}")
        
        try:
            async with websockets.connect(url) as ws:
                self.ws = ws
                self.is_connected = True
                logger.info(f"✅ Connected to Binance {symbol} ticker")
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        update = PriceUpdate(
                            exchange='binance',
                            symbol=symbol,
                            bid=float(data['b']),
                            ask=float(data['a']),
                            bid_size=float(data['B']),
                            ask_size=float(data['A']),
                            timestamp=datetime.now()
                        )
                        await self._emit_price(update)
                    except Exception as e:
                        logger.error(f"Error parsing ticker data: {e}")
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            await self._emit_error(e)


class BybitWebSocketFeed(WebSocketFeed):
    """Bybit WebSocket feed"""
    
    def __init__(self):
        super().__init__('bybit')
        self.base_url = "wss://stream.bybit.com/v5/public/linear"
    
    async def connect_trades(self, symbol: str):
        """Connect to Bybit trade stream"""
        url = self.base_url
        
        logger.info(f"Connecting to Bybit trade stream: {symbol}")
        
        try:
            async with websockets.connect(url) as ws:
                self.ws = ws
                self.is_connected = True
                
                # Subscribe to trades
                subscribe_msg = {
                    "op": "subscribe",
                    "args": [f"publicTrade.{symbol}"]
                }
                await ws.send(json.dumps(subscribe_msg))
                logger.info(f"✅ Connected to Bybit {symbol} trades")
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        if 'data' in data and isinstance(data['data'], list):
                            for trade_data in data['data']:
                                event = TradeEvent(
                                    exchange='bybit',
                                    symbol=symbol,
                                    price=float(trade_data['price']),
                                    quantity=float(trade_data['size']),
                                    side=trade_data['side'].lower(),
                                    timestamp=datetime.fromtimestamp(int(trade_data['time']) / 1000)
                                )
                                await self._emit_trade(event)
                    except Exception as e:
                        logger.error(f"Error parsing trade data: {e}")
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            await self._emit_error(e)


class KrakenWebSocketFeed(WebSocketFeed):
    """Kraken WebSocket feed"""
    
    def __init__(self):
        super().__init__('kraken')
        self.base_url = "wss://ws.kraken.com"
    
    async def connect_ticker(self, symbol: str):
        """Connect to Kraken ticker stream"""
        url = self.base_url
        
        logger.info(f"Connecting to Kraken ticker stream: {symbol}")
        
        try:
            async with websockets.connect(url) as ws:
                self.ws = ws
                self.is_connected = True
                
                # Subscribe to ticker
                subscribe_msg = {
                    "event": "subscribe",
                    "pair": [symbol],
                    "subscription": {"name": "ticker"}
                }
                await ws.send(json.dumps(subscribe_msg))
                logger.info(f"✅ Connected to Kraken {symbol} ticker")
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        if isinstance(data, list) and len(data) >= 2:
                            ticker = data[1]
                            if 'b' in ticker and 'a' in ticker:
                                update = PriceUpdate(
                                    exchange='kraken',
                                    symbol=symbol,
                                    bid=float(ticker['b'][0]),
                                    ask=float(ticker['a'][0]),
                                    bid_size=float(ticker['b'][2]),
                                    ask_size=float(ticker['a'][2]),
                                    timestamp=datetime.now()
                                )
                                await self._emit_price(update)
                    except Exception as e:
                        logger.error(f"Error parsing ticker data: {e}")
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            await self._emit_error(e)


class MultiExchangeWebSocketAggregator:
    """Manage multiple WebSocket feeds"""
    
    def __init__(self):
        self.feeds: Dict[str, WebSocketFeed] = {}
        self.trade_queue = asyncio.Queue()
        self.price_queue = asyncio.Queue()
        self.active_tasks = []
        
        logger.info("MultiExchangeWebSocketAggregator initialized")
    
    def add_feed(self, exchange: str):
        """Add WebSocket feed for exchange"""
        if exchange.lower() == 'binance':
            feed = BinanceWebSocketFeed()
        elif exchange.lower() == 'bybit':
            feed = BybitWebSocketFeed()
        elif exchange.lower() == 'kraken':
            feed = KrakenWebSocketFeed()
        else:
            logger.error(f"Unsupported exchange: {exchange}")
            return
        
        # Register callbacks
        feed.on_trade(self._on_trade)
        feed.on_price(self._on_price)
        
        self.feeds[exchange.lower()] = feed
        logger.info(f"Added {exchange} WebSocket feed")
    
    async def _on_trade(self, event: TradeEvent):
        """Handle trade event"""
        await self.trade_queue.put(event)
    
    async def _on_price(self, update: PriceUpdate):
        """Handle price update"""
        await self.price_queue.put(update)
    
    async def subscribe_trades(self, exchange: str, symbol: str):
        """Subscribe to trade updates"""
        if exchange.lower() not in self.feeds:
            logger.error(f"Feed for {exchange} not found")
            return
        
        task = asyncio.create_task(
            self.feeds[exchange.lower()].connect_trades(symbol)
        )
        self.active_tasks.append(task)
        logger.info(f"Subscribed to {exchange} {symbol} trades")
    
    async def subscribe_ticker(self, exchange: str, symbol: str):
        """Subscribe to ticker updates"""
        if exchange.lower() not in self.feeds:
            logger.error(f"Feed for {exchange} not found")
            return
        
        task = asyncio.create_task(
            self.feeds[exchange.lower()].connect_ticker(symbol)
        )
        self.active_tasks.append(task)
        logger.info(f"Subscribed to {exchange} {symbol} ticker")
    
    async def get_next_trade(self) -> Optional[TradeEvent]:
        """Get next trade event"""
        try:
            return await asyncio.wait_for(self.trade_queue.get(), timeout=30)
        except asyncio.TimeoutError:
            return None
    
    async def get_next_price(self) -> Optional[PriceUpdate]:
        """Get next price update"""
        try:
            return await asyncio.wait_for(self.price_queue.get(), timeout=30)
        except asyncio.TimeoutError:
            return None
    
    async def close_all(self):
        """Close all WebSocket connections"""
        for task in self.active_tasks:
            task.cancel()
        
        await asyncio.gather(*self.active_tasks, return_exceptions=True)
        logger.info("All WebSocket feeds closed")


# Demo usage
async def demo():
    """Demonstrate WebSocket integration"""
    logger.info("\n" + "="*60)
    logger.info("WebSocket Real-Time Feeds Demo")
    logger.info("="*60)
    
    aggregator = MultiExchangeWebSocketAggregator()
    aggregator.add_feed('binance')
    
    logger.info("\n📡 Subscribing to Binance BTC/USDT trades...")
    await aggregator.subscribe_trades('binance', 'BTCUSDT')
    
    logger.info("Receiving trades (ctrl+c to stop)...")
    try:
        for _ in range(5):
            trade = await aggregator.get_next_trade()
            if trade:
                logger.info(f"Trade: {trade.symbol} {trade.side} {trade.quantity}@${trade.price}")
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    finally:
        await aggregator.close_all()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(demo())
