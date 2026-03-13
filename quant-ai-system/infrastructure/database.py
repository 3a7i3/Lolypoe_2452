"""
Database Integration
PostgreSQL for persistent storage + Redis for caching
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psycopg
import redis.asyncio as aioredis
from dataclasses import asdict

logger = logging.getLogger(__name__)


class PostgreSQLManager:
    """PostgreSQL database manager"""
    
    def __init__(self, connection_string: str):
        """Initialize PostgreSQL connection"""
        self.connection_string = connection_string
        self.connection = None
        
        logger.info("PostgreSQLManager initialized")
    
    async def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.connection = await psycopg.AsyncConnection.connect(
                self.connection_string,
                autocommit=False
            )
            logger.info("✅ Connected to PostgreSQL")
            await self._create_tables()
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
    
    async def _create_tables(self):
        """Create necessary tables"""
        tables = [
            # Trades table
            """
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                strategy_id VARCHAR(100),
                symbol VARCHAR(20),
                side VARCHAR(10),
                quantity FLOAT,
                price FLOAT,
                commission FLOAT,
                pnl FLOAT,
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Strategy performance
            """
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id SERIAL PRIMARY KEY,
                strategy_id VARCHAR(100),
                symbol VARCHAR(20),
                total_trades INT,
                win_trades INT,
                loss_trades INT,
                win_rate FLOAT,
                total_return FLOAT,
                sharpe_ratio FLOAT,
                max_drawdown FLOAT,
                profit_factor FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Market data
            """
            CREATE TABLE IF NOT EXISTS market_data (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20),
                exchange VARCHAR(50),
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume FLOAT,
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, exchange, timestamp)
            );
            """,
            
            # Price history
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20),
                exchange VARCHAR(50),
                price FLOAT,
                bid FLOAT,
                ask FLOAT,
                volume FLOAT,
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Signals
            """
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                strategy_id VARCHAR(100),
                symbol VARCHAR(20),
                signal_type VARCHAR(20),
                confidence FLOAT,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Portfolio state
            """
            CREATE TABLE IF NOT EXISTS portfolio_state (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                total_balance FLOAT,
                available_balance FLOAT,
                used_balance FLOAT,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        
        try:
            async with self.connection.cursor() as cur:
                for table_sql in tables:
                    await cur.execute(table_sql)
                await self.connection.commit()
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
    
    async def insert_trade(self, trade_data: Dict) -> int:
        """Insert trade record"""
        try:
            async with self.connection.cursor() as cur:
                await cur.execute("""
                    INSERT INTO trades (strategy_id, symbol, side, quantity, price, commission, pnl, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    trade_data.get('strategy_id'),
                    trade_data.get('symbol'),
                    trade_data.get('side'),
                    trade_data.get('quantity'),
                    trade_data.get('price'),
                    trade_data.get('commission', 0),
                    trade_data.get('pnl', 0),
                    trade_data.get('status', 'EXECUTED')
                ))
                trade_id = await cur.fetchone()
                await self.connection.commit()
                return trade_id[0]
        except Exception as e:
            logger.error(f"Error inserting trade: {e}")
            return None
    
    async def insert_market_data(self, market_data: Dict) -> int:
        """Insert market data"""
        try:
            async with self.connection.cursor() as cur:
                await cur.execute("""
                    INSERT INTO market_data (symbol, exchange, open, high, low, close, volume, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    market_data.get('symbol'),
                    market_data.get('exchange'),
                    market_data.get('open'),
                    market_data.get('high'),
                    market_data.get('low'),
                    market_data.get('close'),
                    market_data.get('volume'),
                    market_data.get('timestamp')
                ))
                data_id = await cur.fetchone()
                await self.connection.commit()
                return data_id[0]
        except Exception as e:
            logger.error(f"Error inserting market data: {e}")
            return None
    
    async def insert_signal(self, signal_data: Dict) -> int:
        """Insert trading signal"""
        try:
            async with self.connection.cursor() as cur:
                await cur.execute("""
                    INSERT INTO signals (strategy_id, symbol, signal_type, confidence, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    signal_data.get('strategy_id'),
                    signal_data.get('symbol'),
                    signal_data.get('signal_type'),
                    signal_data.get('confidence'),
                    json.dumps(signal_data.get('metadata', {}))
                ))
                signal_id = await cur.fetchone()
                await self.connection.commit()
                return signal_id[0]
        except Exception as e:
            logger.error(f"Error inserting signal: {e}")
            return None
    
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades for symbol"""
        try:
            async with self.connection.cursor() as cur:
                await cur.execute("""
                    SELECT * FROM trades
                    WHERE symbol = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (symbol, limit))
                
                columns = [desc[0] for desc in cur.description]
                rows = await cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []
    
    async def get_strategy_performance(self, strategy_id: str) -> Optional[Dict]:
        """Get strategy performance metrics"""
        try:
            async with self.connection.cursor() as cur:
                await cur.execute("""
                    SELECT * FROM strategy_performance
                    WHERE strategy_id = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (strategy_id,))
                
                row = await cur.fetchone()
                if not row:
                    return None
                
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Error fetching strategy performance: {e}")
            return None
    
    async def disconnect(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from PostgreSQL")


class RedisManager:
    """Redis cache manager"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis connection"""
        self.redis_url = redis_url
        self.redis = None
        
        logger.info("RedisManager initialized")
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def set_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache value with TTL"""
        try:
            if isinstance(value, dict) or isinstance(value, list):
                value = json.dumps(value)
            
            await self.redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            value = await self.redis.get(key)
            if not value:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except:
                return value
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """Delete cache key"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False
    
    async def cache_market_data(self, market_data: Dict, ttl: int = 300) -> bool:
        """Cache market data"""
        key = f"market:{market_data['symbol']}:{market_data['exchange']}"
        return await self.set_cache(key, market_data, ttl)
    
    async def get_market_data(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Get cached market data"""
        key = f"market:{symbol}:{exchange}"
        return await self.get_cache(key)
    
    async def cache_signal(self, signal: Dict, ttl: int = 3600) -> bool:
        """Cache trading signal"""
        key = f"signal:{signal['strategy_id']}:{signal['symbol']}"
        return await self.set_cache(key, signal, ttl)
    
    async def get_signal(self, strategy_id: str, symbol: str) -> Optional[Dict]:
        """Get cached signal"""
        key = f"signal:{strategy_id}:{symbol}"
        return await self.get_cache(key)
    
    async def cache_performance(self, strategy_id: str, performance: Dict, ttl: int = 3600) -> bool:
        """Cache strategy performance"""
        key = f"perf:{strategy_id}"
        return await self.set_cache(key, performance, ttl)
    
    async def get_performance(self, strategy_id: str) -> Optional[Dict]:
        """Get cached performance"""
        key = f"perf:{strategy_id}"
        return await self.get_cache(key)
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")


class DatabaseCluster:
    """Combined PostgreSQL + Redis cluster"""
    
    def __init__(self, pg_connection_string: str, redis_url: str = "redis://localhost:6379"):
        self.pg = PostgreSQLManager(pg_connection_string)
        self.redis = RedisManager(redis_url)
    
    async def connect(self):
        """Connect to both databases"""
        await self.pg.connect()
        await self.redis.connect()
        logger.info("✅ Database cluster connected")
    
    async def insert_trade(self, trade_data: Dict) -> Optional[int]:
        """Insert trade and cache it"""
        trade_id = await self.pg.insert_trade(trade_data)
        
        if trade_id:
            cache_key = f"trade:{trade_id}"
            trade_data['id'] = trade_id
            await self.redis.set_cache(cache_key, trade_data, ttl=86400)
        
        return trade_id
    
    async def insert_market_data(self, data: Dict) -> Optional[int]:
        """Insert market data and cache it"""
        await self.redis.cache_market_data(data)
        return await self.pg.insert_market_data(data)
    
    async def insert_signal(self, signal: Dict) -> Optional[int]:
        """Insert signal and cache it"""
        await self.redis.cache_signal(signal)
        return await self.pg.insert_signal(signal)
    
    async def disconnect(self):
        """Close all connections"""
        await self.pg.disconnect()
        await self.redis.disconnect()
        logger.info("Database cluster disconnected")


# Demo usage
async def demo():
    """Demonstrate database integration"""
    logger.info("\n" + "="*60)
    logger.info("Database Integration Demo")
    logger.info("="*60)
    
    # Note: You would need PostgreSQL and Redis running locally
    try:
        db = DatabaseCluster(
            pg_connection_string="postgresql://user:password@localhost/crypto_ai",
            redis_url="redis://localhost:6379"
        )
        
        await db.connect()
        
        # Insert sample trade
        trade = {
            'strategy_id': 'STRAT_001',
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'quantity': 0.1,
            'price': 42000,
            'commission': 10,
            'pnl': 0,
            'status': 'EXECUTED'
        }
        
        trade_id = await db.insert_trade(trade)
        logger.info(f"✅ Trade inserted with ID: {trade_id}")
        
        # Insert market data
        market_data = {
            'symbol': 'BTC/USDT',
            'exchange': 'binance',
            'open': 41900,
            'high': 42100,
            'low': 41800,
            'close': 42050,
            'volume': 1000,
            'timestamp': datetime.now()
        }
        
        data_id = await db.insert_market_data(market_data)
        logger.info(f"✅ Market data inserted with ID: {data_id}")
        
        await db.disconnect()
        
    except Exception as e:
        logger.error(f"Error in demo: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(demo())
