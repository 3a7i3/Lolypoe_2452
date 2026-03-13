"""
Market Scanner - Monitor 1500+ cryptocurrencies across multiple exchanges
Institutional-grade market monitoring with Bybit, Binance, Coinbase, Kraken support
"""

import asyncio
import logging
from typing import Dict, List, Tuple
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Per-exchange rate limiter for institutional compliance"""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.requests = []
    
    async def wait(self):
        """Wait if rate limit exceeded"""
        now = datetime.now()
        # Remove requests outside time window
        self.requests = [t for t in self.requests if (now - t).total_seconds() < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]).total_seconds() + 0.1
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                self.requests = []
        
        self.requests.append(datetime.now())

class MarketScanner:
    """Monitor 1500+ cryptocurrencies across institutional exchanges"""
    
    def __init__(self):
        self.exchanges = self._initialize_exchanges()
        self.rate_limiters = self._initialize_rate_limiters()
        self.market_cache = {}
        self.exchange_stats = defaultdict(lambda: {'scans': 0, 'symbols': 0, 'last_scan': None})
        self.last_scan = None
        self.anomalies_detected = []
        logger.info(f"✓ Market Scanner v2 initialized with {len(self.exchanges)} exchanges")
        logger.info(f"✓ Universe size: {config.CRYPTO_UNIVERSE_SIZE} cryptos")
    
    def _initialize_exchanges(self) -> Dict:
        """Initialize CCXT exchange objects with institutional settings"""
        exchanges = {}
        
        for exchange_name, config_dict in config.EXCHANGES.items():
            if not config_dict['enabled']:
                continue
                
            try:
                exchange_class = getattr(ccxt, exchange_name)
                exchange = exchange_class({
                    'enableRateLimit': True,
                    'timeout': 30000,
                    'rateLimit': 1000 // config_dict['rate_limit'],  # ms per request
                    'fetch2': True,  # Use newer API
                })
                exchanges[exchange_name] = exchange
                logger.info(f"✓ {exchange_name} initialized (weight: {config_dict['weight']}, "
                           f"limit: {config_dict['fetch_limit']}, rate: {config_dict['rate_limit']}/min)")
            except Exception as e:
                logger.error(f"Failed to initialize {exchange_name}: {e}")
        
        return exchanges
    
    def _initialize_rate_limiters(self) -> Dict[str, RateLimiter]:
        """Initialize rate limiters per exchange"""
        limiters = {}
        for exchange_name, config_dict in config.EXCHANGES.items():
            if config_dict['enabled']:
                # Convert rate limit (per minute) to per-second approximation
                max_per_second = config_dict['rate_limit'] / 60
                limiters[exchange_name] = RateLimiter(
                    max_requests=max(1, int(max_per_second)),
                    time_window=1  # per second
                )
        return limiters
    
    async def scan_crypto_universe(self) -> Dict:
        """
        Scan 1500+ cryptocurrencies across all exchanges with intelligent distribution
        Returns: {symbol: {price, volume, change, timestamp, exchanges, volatility, anomalies}}
        """
        market_data = {}
        scan_start = datetime.now()
        
        try:
            # Distribute scanning across exchanges by weight and fetch limit
            tasks = []
            total_to_scan = config.CRYPTO_UNIVERSE_SIZE
            
            for exchange_name, config_dict in config.EXCHANGES.items():
                if config_dict['enabled']:
                    # Allocate based on weight
                    allocation = int(total_to_scan * config_dict['weight'])
                    logger.info(f"Allocating {allocation} symbols to {exchange_name}")
                    tasks.append(self._scan_exchange_async(exchange_name, allocation))
            
            # Run all scans concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Merge results
            for result in results:
                if isinstance(result, dict):
                    for symbol, data in result.items():
                        if symbol not in market_data:
                            market_data[symbol] = data
                        else:
                            # Aggregate multi-exchange data
                            if 'exchanges' not in market_data[symbol]:
                                market_data[symbol]['exchanges'] = [market_data[symbol].get('exchange')]
                            market_data[symbol]['exchanges'].append(data.get('exchange'))
            
            self.market_cache = market_data
            self.last_scan = datetime.now()
            scan_duration = (self.last_scan - scan_start).total_seconds()
            
            logger.info(f"✓ Completed scan of {len(market_data)} unique symbols in {scan_duration:.2f}s")
            logger.info(f"  Average: {len(market_data)/scan_duration:.1f} symbols/sec")
            
            return market_data
            
        except Exception as e:
            logger.error(f"Market scan error: {e}")
            return self.market_cache or {}
    
    async def _scan_exchange_async(self, exchange_name: str, limit: int = 300) -> Dict:
        """Scan single exchange with rate limiting and error handling"""
        data = {}
        config_dict = config.EXCHANGES.get(exchange_name, {})
        
        try:
            exchange = self.exchanges[exchange_name]
            rate_limiter = self.rate_limiters[exchange_name]
            
            # Load markets
            await rate_limiter.wait()
            exchange.load_markets()
            
            # Get symbols respecting fetch_limit
            all_symbols = list(exchange.symbols)
            fetch_limit = min(limit, config_dict.get('fetch_limit', 300))
            symbols_to_scan = all_symbols[:fetch_limit]
            
            logger.debug(f"Scanning {len(symbols_to_scan)} symbols on {exchange_name}")
            
            # Fetch tickers in batches
            batch_size = min(50, fetch_limit // 5 + 1)  # Smart batching
            
            for i in range(0, len(symbols_to_scan), batch_size):
                batch = symbols_to_scan[i:i+batch_size]
                
                for symbol in batch:
                    try:
                        await rate_limiter.wait()  # Respect rate limits
                        
                        # Fetch ticker
                        ticker = exchange.fetch_ticker(symbol)
                        
                        data[symbol] = {
                            'symbol': symbol,
                            'price': ticker.get('last'),
                            'high': ticker.get('high'),
                            'low': ticker.get('low'),
                            'bid': ticker.get('bid'),
                            'ask': ticker.get('ask'),
                            'bid_ask_spread': self._calculate_bid_ask_spread(ticker),
                            'volume_usd': ticker.get('quoteVolume'),
                            'volume_coin': ticker.get('baseVolume'),
                            'change_percent': ticker.get('percentage'),
                            'timestamp': ticker.get('timestamp'),
                            'exchange': exchange_name,
                            'datetime': ticker.get('datetime'),
                        }
                        
                    except ccxt.RateLimitExceeded:
                        await asyncio.sleep(1)  # Back off on rate limit
                        continue
                    except Exception as e:
                        logger.debug(f"Error fetching {symbol} on {exchange_name}: {e}")
                        continue
            
            self.exchange_stats[exchange_name]['scans'] += 1
            self.exchange_stats[exchange_name]['symbols'] = len(data)
            self.exchange_stats[exchange_name]['last_scan'] = datetime.now()
            
            logger.info(f"✓ Scanned {len(data)} symbols on {exchange_name} "
                       f"(fetch_limit: {fetch_limit}, actual: {len(data)})")
            
        except Exception as e:
            logger.error(f"Exchange scan error ({exchange_name}): {e}")
        
        return data
    
    @staticmethod
    def _calculate_bid_ask_spread(ticker: Dict) -> float:
        """Calculate bid-ask spread percentage"""
        bid = ticker.get('bid', 0)
        ask = ticker.get('ask', 0)
        
        if bid and ask and bid > 0:
            return (ask - bid) / bid * 100
        return 0.0
    
    async def fetch_ohlcv_multi_exchange(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Dict:
        """
        Fetch OHLCV from multiple exchanges for comparison
        Returns: {exchange_name: ohlcv_data}
        """
        results = {}
        
        try:
            tasks = []
            for exchange_name in self.exchanges:
                tasks.append(self._fetch_ohlcv_single(exchange_name, symbol, timeframe, limit))
            
            ohlcv_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for exchange_name, ohlcv_data in zip(self.exchanges.keys(), ohlcv_results):
                if isinstance(ohlcv_data, list):
                    results[exchange_name] = ohlcv_data
            
            return results
            
        except Exception as e:
            logger.error(f"Multi-exchange OHLCV error for {symbol}: {e}")
            return {}
    
    async def _fetch_ohlcv_single(self, exchange_name: str, symbol: str, 
                                   timeframe: str, limit: int) -> List:
        """Fetch OHLCV from single exchange"""
        try:
            rate_limiter = self.rate_limiters.get(exchange_name)
            if rate_limiter:
                await rate_limiter.wait()
            
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                return []
            
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
            
        except Exception as e:
            logger.debug(f"OHLCV error {symbol} on {exchange_name}: {e}")
            return []
    
    async def get_market_depth(self, symbol: str, exchange_name: str = 'binance', 
                               limit: int = 20) -> Dict:
        """
        Get order book depth for a symbol with rate limiting
        Returns: {bids, asks, timestamp}
        """
        try:
            rate_limiter = self.rate_limiters.get(exchange_name)
            if rate_limiter:
                await rate_limiter.wait()
            
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                logger.warning(f"Exchange {exchange_name} not available")
                return {}
            
            orderbook = exchange.fetch_order_book(symbol, limit=limit)
            
            return {
                'symbol': symbol,
                'exchange': exchange_name,
                'bids': orderbook.get('bids', []),
                'asks': orderbook.get('asks', []),
                'timestamp': orderbook.get('timestamp'),
                'bid_volume': sum([b[1] for b in orderbook.get('bids', [])[:limit]]),
                'ask_volume': sum([a[1] for a in orderbook.get('asks', [])[:limit]]),
            }
            
        except Exception as e:
            logger.debug(f"Order book error for {symbol}: {e}")
            return {}
    
    async def get_recent_trades(self, symbol: str, exchange_name: str = 'binance', 
                                limit: int = 50) -> List:
        """
        Get recent trades for a symbol with rate limiting
        Returns: list of recent trades with metadata
        """
        try:
            rate_limiter = self.rate_limiters.get(exchange_name)
            if rate_limiter:
                await rate_limiter.wait()
            
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                return []
            
            trades = exchange.fetch_trades(symbol, limit=limit)
            
            return [{
                'id': t.get('id'),
                'symbol': t.get('symbol'),
                'timestamp': t.get('timestamp'),
                'price': t.get('price'),
                'amount': t.get('amount'),
                'side': t.get('side'),
                'exchange': exchange_name
            } for t in trades]
            
        except Exception as e:
            logger.debug(f"Trades error for {symbol}: {e}")
            return []
    
    def get_top_gainers(self, top_n: int = 20, min_volume: float = 10000) -> List:
        """
        Get top gainers (filtered by minimum volume)
        Returns: list of (symbol, data) tuples
        """
        try:
            filtered = {
                s: d for s, d in self.market_cache.items()
                if d.get('volume_usd', 0) >= min_volume and d.get('change_percent')
            }
            
            sorted_symbols = sorted(
                filtered.items(),
                key=lambda x: x[1].get('change_percent', 0),
                reverse=True
            )
            
            return sorted_symbols[:top_n]
        except Exception as e:
            logger.error(f"Top gainers error: {e}")
            return []
    
    def get_top_losers(self, top_n: int = 20, min_volume: float = 10000) -> List:
        """
        Get top losers (filtered by minimum volume)
        Returns: list of (symbol, data) tuples
        """
        try:
            filtered = {
                s: d for s, d in self.market_cache.items()
                if d.get('volume_usd', 0) >= min_volume and d.get('change_percent')
            }
            
            sorted_symbols = sorted(
                filtered.items(),
                key=lambda x: x[1].get('change_percent', 0)
            )
            
            return sorted_symbols[:top_n]
        except Exception as e:
            logger.error(f"Top losers error: {e}")
            return []
    
    def get_top_volume(self, top_n: int = 20) -> List:
        """Get top coins by volume"""
        try:
            sorted_symbols = sorted(
                self.market_cache.items(),
                key=lambda x: x[1].get('volume_usd', 0),
                reverse=True
            )
            return sorted_symbols[:top_n]
        except Exception as e:
            logger.error(f"Top volume error: {e}")
            return []
    
    def get_market_summary(self) -> Dict:
        """Get comprehensive market summary statistics"""
        try:
            changes = [d.get('change_percent', 0) for d in self.market_cache.values() 
                      if d.get('change_percent') is not None]
            volumes = [d.get('volume_usd', 0) for d in self.market_cache.values() 
                      if d.get('volume_usd')]
            prices = [d.get('price', 0) for d in self.market_cache.values() 
                     if d.get('price')]
            
            return {
                'total_symbols': len(self.market_cache),
                'total_exchanges': len(self.exchanges),
                'avg_change_percent': sum(changes) / len(changes) if changes else 0,
                'total_volume_usd': sum(volumes),
                'avg_price': sum(prices) / len(prices) if prices else 0,
                'gainers_count': len([c for c in changes if c > 0]),
                'losers_count': len([c for c in changes if c < 0]),
                'symbols_up_percent': len([c for c in changes if c > 0]) / len(changes) * 100 if changes else 0,
                'last_scan': self.last_scan.isoformat() if self.last_scan else None,
                'exchange_stats': dict(self.exchange_stats)
            }
        except Exception as e:
            logger.error(f"Market summary error: {e}")
            return {}
    
    def get_exchange_specific_data(self, exchange_name: str) -> Dict:
        """Get all data for specific exchange"""
        try:
            exchange_data = {
                s: d for s, d in self.market_cache.items()
                if d.get('exchange') == exchange_name
            }
            return exchange_data
        except Exception as e:
            logger.error(f"Exchange {exchange_name} data error: {e}")
            return {}
    
    def detect_arbitrage_opportunities(self, min_spread: float = 0.5) -> List[Dict]:
        """
        Detect arbitrage opportunities across exchanges
        Returns: list of {symbol, buy_exchange, sell_exchange, spread_percent, profit}
        """
        opportunities = []
        
        try:
            # Group by symbol across exchanges
            symbol_data = defaultdict(list)
            for symbol, data in self.market_cache.items():
                symbol_data[symbol].append(data)
            
            # Find symbols trading on multiple exchanges
            for symbol, exchange_data in symbol_data.items():
                if len(exchange_data) >= 2:
                    prices = sorted(exchange_data, key=lambda x: x.get('price', 0))
                    buy_price = prices[0].get('price', 0)
                    sell_price = prices[-1].get('price', 0)
                    
                    if buy_price > 0:
                        spread = ((sell_price - buy_price) / buy_price) * 100
                        
                        if spread >= min_spread:
                            opportunities.append({
                                'symbol': symbol,
                                'buy_exchange': prices[0].get('exchange'),
                                'buy_price': buy_price,
                                'sell_exchange': prices[-1].get('exchange'),
                                'sell_price': sell_price,
                                'spread_percent': spread,
                                'estimated_profit_percent': spread - 0.5,  # after fees
                                'timestamp': datetime.now().isoformat()
                            })
            
            # Sort by spread
            opportunities.sort(key=lambda x: x['spread_percent'], reverse=True)
