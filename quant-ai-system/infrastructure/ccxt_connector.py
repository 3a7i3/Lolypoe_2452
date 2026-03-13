"""
CCXT Exchange Integration
Real-time market data from Binance, Bybit, Kraken, Coinbase
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import ccxt
import ccxt.async_support as ccxt_async
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExchangeConnector:
    """Base class for exchange connections"""
    
    def __init__(self, exchange_name: str, api_key: str = "", api_secret: str = ""):
        """Initialize exchange connector"""
        self.exchange_name = exchange_name.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = None
        self.connected = False
        
        logger.info(f"Initializing {exchange_name} connector (Public mode)")
    
    async def connect(self):
        """Connect to exchange"""
        try:
            exchange_class = getattr(ccxt_async, self.exchange_name)
            config = {
                'enableRateLimit': True,
                'asyncio_loop': asyncio.get_event_loop(),
            }
            
            if self.api_key and self.api_secret:
                config['apiKey'] = self.api_key
                config['secret'] = self.api_secret
            
            self.exchange = exchange_class(config)
            self.connected = True
            logger.info(f"✅ Connected to {self.exchange_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to {self.exchange_name}: {e}")
            raise
    
    async def disconnect(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()
            self.connected = False
            logger.info(f"Disconnected from {self.exchange_name}")
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price ticker"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'exchange': self.exchange_name,
                'symbol': symbol,
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'last': ticker.get('last'),
                'volume': ticker.get('quoteVolume'),
                'timestamp': datetime.fromtimestamp(ticker['timestamp'] / 1000),
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    async def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Get OHLCV candlestick data"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            df['exchange'] = self.exchange_name
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return None
    
    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Get order book (bid/ask levels)"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=limit)
            return {
                'exchange': self.exchange_name,
                'symbol': symbol,
                'bids': orderbook['bids'][:limit],
                'asks': orderbook['asks'][:limit],
                'timestamp': datetime.fromtimestamp(orderbook['timestamp'] / 1000),
            }
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return None
    
    async def get_markets(self) -> List[str]:
        """Get all available trading pairs"""
        try:
            await self.exchange.load_markets()
            symbols = [s for s in self.exchange.symbols if '/' in s]
            logger.info(f"✅ Loaded {len(symbols)} symbols from {self.exchange_name}")
            return symbols
        except Exception as e:
            logger.error(f"Error loading markets: {e}")
            return []


class MultiExchangeAggregator:
    """Aggregate data from multiple exchanges"""
    
    def __init__(self):
        self.connectors: Dict[str, ExchangeConnector] = {}
        self.market_data = {}
        
        logger.info("MultiExchangeAggregator initialized")
    
    async def add_exchange(self, exchange_name: str, api_key: str = "", api_secret: str = ""):
        """Add exchange connector"""
        connector = ExchangeConnector(exchange_name, api_key, api_secret)
        await connector.connect()
        self.connectors[exchange_name.lower()] = connector
        logger.info(f"Added {exchange_name} to aggregator")
    
    async def remove_exchange(self, exchange_name: str):
        """Remove exchange connector"""
        if exchange_name.lower() in self.connectors:
            await self.connectors[exchange_name.lower()].disconnect()
            del self.connectors[exchange_name.lower()]
            logger.info(f"Removed {exchange_name} from aggregator")
    
    async def get_best_price(self, symbol: str, order_type: str = 'buy') -> Optional[Dict]:
        """Get best bid/ask across exchanges"""
        prices = []
        
        tasks = [
            connector.get_ticker(symbol)
            for connector in self.connectors.values()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict) and result:
                prices.append(result)
        
        if not prices:
            return None
        
        if order_type == 'buy':
            # Best buy = lowest ask
            best = min(prices, key=lambda x: x['ask'])
        else:
            # Best sell = highest bid
            best = max(prices, key=lambda x: x['bid'])
        
        return best
    
    async def get_arbitrage_opportunities(self, symbol: str, threshold: float = 0.5) -> List[Dict]:
        """Find arbitrage opportunities between exchanges"""
        opportunities = []
        tickers = {}
        
        tasks = [
            connector.get_ticker(symbol)
            for connector in self.connectors.values()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict) and result:
                tickers[result['exchange']] = result
        
        # Find buy opportunity (lowest ask) and sell (highest bid)
        exchanges = list(tickers.keys())
        for i, buy_exchange in enumerate(exchanges):
            for sell_exchange in exchanges[i+1:]:
                buy_price = tickers[buy_exchange]['ask']
                sell_price = tickers[sell_exchange]['bid']
                profit_pct = ((sell_price - buy_price) / buy_price) * 100
                
                if profit_pct > threshold:
                    opportunities.append({
                        'symbol': symbol,
                        'buy_exchange': buy_exchange,
                        'buy_price': buy_price,
                        'sell_exchange': sell_exchange,
                        'sell_price': sell_price,
                        'profit_pct': profit_pct,
                        'timestamp': datetime.now(),
                    })
        
        return opportunities
    
    async def get_market_snapshot(self, symbols: List[str]) -> Dict[str, Any]:
        """Get aggregated market data snapshot"""
        snapshot = {
            'timestamp': datetime.now(),
            'exchanges': list(self.connectors.keys()),
            'data': {}
        }
        
        for symbol in symbols:
            tickers = await asyncio.gather(*[
                connector.get_ticker(symbol)
                for connector in self.connectors.values()
            ], return_exceptions=True)
            
            snapshot['data'][symbol] = [t for t in tickers if isinstance(t, dict)]
        
        return snapshot
    
    async def close_all(self):
        """Close all exchange connections"""
        tasks = [connector.disconnect() for connector in self.connectors.values()]
        await asyncio.gather(*tasks)
        logger.info("All exchange connections closed")


class LiveMarketDataFeeder:
    """Continuously feed live market data to trading system"""
    
    def __init__(self, aggregator: MultiExchangeAggregator):
        self.aggregator = aggregator
        self.is_running = False
        self.market_data_queue = asyncio.Queue()
        self.update_interval = 5  # seconds
        
        logger.info("LiveMarketDataFeeder initialized")
    
    async def start(self):
        """Start data feed"""
        self.is_running = True
        logger.info("LiveMarketDataFeeder started")
        await self._feed_loop()
    
    async def stop(self):
        """Stop data feed"""
        self.is_running = False
        logger.info("LiveMarketDataFeeder stopped")
    
    async def _feed_loop(self):
        """Main data feed loop"""
        while self.is_running:
            try:
                # Get market data from all exchanges
                snapshot = await self.aggregator.get_market_snapshot([
                    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT'
                ])
                
                # Put in queue for trading system
                await self.market_data_queue.put(snapshot)
                
                logger.debug(f"Market data snapshot queued: {len(snapshot['data'])} symbols")
                
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in feed loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def get_data(self) -> Dict[str, Any]:
        """Get next market data from queue"""
        return await self.market_data_queue.get()


# Demo usage
async def demo():
    """Demonstrate CCXT integration"""
    logger.info("\n" + "="*60)
    logger.info("CCXT Integration Demo")
    logger.info("="*60)
    
    aggregator = MultiExchangeAggregator()
    
    try:
        # Add exchanges (public mode only)
        await aggregator.add_exchange('binance')
        await aggregator.add_exchange('bybit')
        await aggregator.add_exchange('kraken')
        
        logger.info("\n📊 Fetching BTC/USDT prices from exchanges...")
        best_price = await aggregator.get_best_price('BTC/USDT', 'buy')
        logger.info(f"✅ Best BTC/USDT buy price: ${best_price['ask']} on {best_price['exchange']}")
        
        logger.info("\n🔍 Checking arbitrage opportunities...")
        opportunities = await aggregator.get_arbitrage_opportunities('ETH/USDT', threshold=0.1)
        if opportunities:
            for opp in opportunities:
                logger.info(f"   Arbitrage: Buy on {opp['buy_exchange']} → Sell on {opp['sell_exchange']}")
                logger.info(f"   Profit: {opp['profit_pct']:.2f}%")
        else:
            logger.info("   No arbitrage opportunities found")
        
        logger.info("\n📈 Market snapshot...")
        snapshot = await aggregator.get_market_snapshot(['BTC/USDT', 'ETH/USDT'])
        for symbol, data in snapshot['data'].items():
            if data:
                logger.info(f"   {symbol}: {len(data)} exchange prices available")
        
    finally:
        await aggregator.close_all()
        logger.info("\n✅ Demo completed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(demo())
