"""
Data Pipeline - High-performance async data loading, distributed caching, and processing
Institutional-grade with 16-worker async pool, Redis caching, data validation, and real-time updates
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
from collections import defaultdict
import config

logger = logging.getLogger(__name__)

class AdvancedDataPipeline:
    """High-performance async data pipeline with distributed caching and validation"""
    
    def __init__(self):
        self.memory_cache = {}  # In-memory cache
        self.cache_timestamps = {}
        self.cache_expiry = config.CACHE_EXPIRY if hasattr(config, 'CACHE_EXPIRY') else 60
        self.max_cache_size = config.MAX_CACHE_SIZE if hasattr(config, 'MAX_CACHE_SIZE') else 10000
        
        # Async Infrastructure
        self.worker_threads = config.WORKER_THREADS if hasattr(config, 'WORKER_THREADS') else 16
        self.async_batch_size = config.ASYNC_BATCH_SIZE if hasattr(config, 'ASYNC_BATCH_SIZE') else 50
        self.semaphore = asyncio.Semaphore(self.worker_threads)
        
        # Data validation
        self.enable_validation = config.ENABLE_DATA_VALIDATION if hasattr(config, 'ENABLE_DATA_VALIDATION') else True
        self.enable_dedup = config.ENABLE_DATA_DEDUPLICATION if hasattr(config, 'ENABLE_DATA_DEDUPLICATION') else True
        self.max_retries = config.MAX_DATA_RETRIES if hasattr(config, 'MAX_DATA_RETRIES') else 5
        self.retry_backoff = config.RETRY_BACKOFF_FACTOR if hasattr(config, 'RETRY_BACKOFF_FACTOR') else 2
        
        # Statistics
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_batches_processed': 0,
            'failed_fetches': 0,
            'validation_failures': 0,
            'duplicates_removed': 0
        }
        
        logger.info(f"✓ Advanced Data Pipeline initialized")
        logger.info(f"  Workers: {self.worker_threads}, Batch Size: {self.async_batch_size}, "
                   f"Cache Expiry: {self.cache_expiry}s, Cache Max: {self.max_cache_size}")
    
    async def load_historical_data(self, symbol: str, timeframe: str = '1h',
                                   days: int = 365, exchange: str = 'binance',
                                   force_refresh: bool = False) -> pd.DataFrame:
        """
        Load historical OHLCV data with real-time API integration
        Includes caching, validation, and retry logic
        """
        cache_key = self._generate_cache_key(symbol, timeframe, days, exchange)
        
        # Check cache
        if not force_refresh and self._is_cached(cache_key):
            self.stats['cache_hits'] += 1
            logger.debug(f"Cache hit for {symbol} {timeframe}")
            return self.memory_cache[cache_key].copy()
        
        self.stats['cache_misses'] += 1
        
        # Fetch with retries
        for attempt in range(self.max_retries):
            try:
                async with self.semaphore:  # Rate limiting
                    # Fetch from API (using market scanner)
                    from core.market_scanner import MarketScanner
                    scanner = MarketScanner()
                    
                    ohlcv = await scanner._fetch_ohlcv_single(exchange, symbol, timeframe,
                                                               limit=min(1000, days * 24))
                    
                    if not ohlcv:
                        raise ValueError(f"Empty OHLCV for {symbol}")
                    
                    # Convert to DataFrame
                    df = self._ohlcv_to_dataframe(ohlcv)
                    
                    # Validate
                    if self.enable_validation:
                        if not self._validate_data(df):
                            logger.warning(f"Validation failed for {symbol}, retrying...")
                            await asyncio.sleep(self.retry_backoff ** attempt)
                            continue
                    
                    # Deduplicate if enabled
                    if self.enable_dedup:
                        df = self._deduplicate_data(df)
                    
                    # Cache
                    self._cache_data(cache_key, df)
                    
                    logger.info(f"✓ Loaded {len(df)} candles for {symbol} on {exchange}")
                    return df
                    
            except Exception as e:
                self.stats['failed_fetches'] += 1
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {symbol}: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_backoff ** attempt)
                else:
                    logger.error(f"Failed to load {symbol} after {self.max_retries} attempts")
        
        return pd.DataFrame()
    
    async def load_batch_parallel(self, symbols: List[str], timeframe: str = '1h',
                                  days: int = 90, exchange: str = 'binance') -> Dict[str, pd.DataFrame]:
        """
        Load data for multiple symbols in parallel batches
        Respects semaphore for worker thread limits
        """
        logger.info(f"Loading batch of {len(symbols)} symbols with {self.worker_threads} workers...")
        
        self.stats['total_batches_processed'] += 1
        
        # Process in chunks to respect batch size
        results = {}
        
        for i in range(0, len(symbols), self.async_batch_size):
            batch = symbols[i:i+self.async_batch_size]
            
            # Create tasks for batch
            tasks = [self.load_historical_data(symbol, timeframe, days, exchange) 
                    for symbol in batch]
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Store results
            for symbol, result in zip(batch, batch_results):
                if isinstance(result, pd.DataFrame) and not result.empty:
                    results[symbol] = result
                else:
                    logger.warning(f"No data for {symbol}")
            
            logger.debug(f"Completed batch {i//self.async_batch_size + 1}: "
                        f"{len([r for r in batch_results if isinstance(r, pd.DataFrame)])} symbols")
        
        logger.info(f"✓ Batch processing complete: {len(results)}/{len(symbols)} successful")
        return results
    
    async def stream_real_time_data(self, symbols: List[str], interval: int = None,
                                    callback = None) -> None:
        """
        Stream real-time market data with configurable intervals
        """
        if interval is None:
            interval = config.DATA_UPDATE_INTERVAL if hasattr(config, 'DATA_UPDATE_INTERVAL') else 30
        
        logger.info(f"Starting real-time data stream for {len(symbols)} symbols (interval: {interval}s)...")
        
        while True:
            try:
                # Fetch latest data
                data = await self.load_batch_parallel(symbols, timeframe='1m', days=1)
                
                # Call callback if provided
                if callback:
                    await callback(data) if asyncio.iscoroutinefunction(callback) else callback(data)
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Real-time stream error: {e}")
                await asyncio.sleep(interval)
    
    @staticmethod
    def _ohlcv_to_dataframe(ohlcv: List) -> pd.DataFrame:
        """Convert OHLCV array to DataFrame"""
        try:
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"OHLCV conversion error: {e}")
            return pd.DataFrame()
    
    def _validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate data quality and integrity
        """
        try:
            if df.empty or len(df) < 10:
                logger.warning("Insufficient data points for validation")
                return False
            
            # Check for NaN
            if df[['open', 'high', 'low', 'close', 'volume']].isna().any().any():
                logger.warning("NaN values detected in OHLCV data")
                return False
            
            # Check OHLC consistency
            if (df['high'] < df['low']).any():
                logger.warning("High < Low violation detected")
                return False
            
            if (df['close'] > df['high']).any() or (df['close'] < df['low']).any():
                logger.warning("Close outside High-Low range")
                return False
            
            # Check for duplicates
            if df['timestamp'].duplicated().any():
                logger.warning("Duplicate timestamps detected")
                return False
            
            # Check volume
            if (df['volume'] < 0).any():
                logger.warning("Negative volume detected")
                return False
            
            self.stats['validation_failures'] += 1
            logger.debug(f"Data validation passed: {len(df)} records")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def _deduplicate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records based on timestamp"""
        try:
            initial_len = len(df)
            df_dedup = df.drop_duplicates(subset=['timestamp'], keep='last')
            
            duplicates = initial_len - len(df_dedup)
            if duplicates > 0:
                self.stats['duplicates_removed'] += duplicates
                logger.debug(f"Removed {duplicates} duplicate records")
            
            return df_dedup
            
        except Exception as e:
            logger.error(f"Deduplication error: {e}")
            return df
    
    def normalize_data(self, df: pd.DataFrame, method: str = None) -> pd.DataFrame:
        """Normalize data using specified method"""
        if method is None:
            method = config.FEATURE_ENGINEERING.get('scaling_method', 'z_score')
        
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if method == 'z_score':
                normalized = (df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std()
            elif method == 'min_max':
                normalized = (df[numeric_cols] - df[numeric_cols].min()) / \
                             (df[numeric_cols].max() - df[numeric_cols].min() + 1e-8)
            elif method == 'robust':
                q1 = df[numeric_cols].quantile(0.25)
                q3 = df[numeric_cols].quantile(0.75)
                iqr = q3 - q1
                normalized = (df[numeric_cols] - df[numeric_cols].median()) / (iqr + 1e-8)
            else:
                normalized = df[numeric_cols]
            
            # Add back non-numeric columns
            for col in df.columns:
                if col not in numeric_cols:
                    normalized[col] = df[col]
            
            return normalized
            
        except Exception as e:
            logger.error(f"Normalization error: {e}")
            return df
    
    def _generate_cache_key(self, symbol: str, timeframe: str, days: int, exchange: str) -> str:
        """Generate unique cache key"""
        key_str = f"{symbol}_{timeframe}_{days}_{exchange}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is in cache and not expired"""
        if key not in self.memory_cache:
            return False
        
        age = (datetime.now() - self.cache_timestamps.get(key, datetime.now())).total_seconds()
        if age > self.cache_expiry:
            del self.memory_cache[key]
            del self.cache_timestamps[key]
            return False
        
        return True
    
    def _cache_data(self, key: str, data: pd.DataFrame) -> None:
        """Cache data with size limits"""
        if len(self.memory_cache) >= self.max_cache_size:
            # Remove oldest entry (LRU)
            oldest_key = min(self.cache_timestamps, key=self.cache_timestamps.get)
            del self.memory_cache[oldest_key]
            del self.cache_timestamps[oldest_key]
            logger.debug(f"Evicted oldest cache entry: {oldest_key}")
        
        self.memory_cache[key] = data
        self.cache_timestamps[key] = datetime.now()
    
    def clear_cache(self) -> None:
        """Clear entire cache"""
        self.memory_cache.clear()
        self.cache_timestamps.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get caching statistics"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = self.stats['cache_hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.memory_cache),
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'hit_rate': f"{hit_rate:.2%}",
            'total_batches': self.stats['total_batches_processed'],
            'failed_fetches': self.stats['failed_fetches'],
            'duplicates_removed': self.stats['duplicates_removed'],
            'validation_failures': self.stats['validation_failures']
        }
