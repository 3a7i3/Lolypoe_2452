
import pandas as pd
from .cex import CEXCollector
from .dex import DEXCollector
from .storage import Storage
from .utils import normalize_symbol
import logging
import time
import os

logger = logging.getLogger("DataEngine")
logger.setLevel(logging.DEBUG)

class DataCollector:
    def __init__(self):
        self.cex = CEXCollector()
        self.storage = Storage()
        self.max_retries = 3

    def fetch_with_retry(self, func, *args, **kwargs):
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {e}")
                time.sleep(1)
        logger.error("All retries failed")
        return None

    def fetch_ohlcv(self, symbol, source="cex", timeframe="1h", save=True, dex_name="uniswap"):
        symbol_norm = normalize_symbol(symbol)
        logger.info(f"Fetching OHLCV {symbol_norm} from {source} tf={timeframe} dex={dex_name}")

        filename = f"{symbol_norm}_{source}_{timeframe}.csv"
        # Cache locale : si fichier existe et <24h, skip fetch
        if os.path.exists(os.path.join("data_storage", filename)):
            mtime = os.path.getmtime(os.path.join("data_storage", filename))
            if time.time() - mtime < 86400:
                logger.info(f"Cache hit: {filename}")
                return self.storage.load_csv(filename)

        if source == "cex":
            func = self.cex.fetch_ohlcv
            df = self.fetch_with_retry(func, symbol_norm, timeframe=timeframe)
        elif source == "dex":
            dex = DEXCollector(dex=dex_name)
            df = self.fetch_with_retry(dex.fetch_ohlcv, symbol_norm, timeframe=timeframe)
        else:
            logger.error(f"Unknown source: {source}")
            return pd.DataFrame()

        if df is not None and save:
            self.storage.save_csv(df, filename)
        return df

    def fetch_orderbook(self, symbol, source="cex"):
        symbol_norm = normalize_symbol(symbol)
        logging.info(f"Fetching orderbook for {symbol_norm} from {source}")
        func = self.cex.fetch_orderbook if source == "cex" else self.dex.fetch_orderbook
        return self.fetch_with_retry(func, symbol_norm) or {}

    def fetch_funding(self, symbol, source="cex"):
        symbol_norm = normalize_symbol(symbol)
        logging.info(f"Fetching funding rates for {symbol_norm} from {source}")
        if source == "cex":
            return self.fetch_with_retry(self.cex.fetch_funding_rates, symbol_norm) or {}
        logging.warning("Funding rates not available for DEX")
        return {}

    def fetch_liquidations(self, symbol, source="cex"):
        symbol_norm = normalize_symbol(symbol)
        logging.info(f"Fetching liquidations for {symbol_norm} from {source}")
        if source == "cex":
            return self.fetch_with_retry(self.cex.fetch_liquidations, symbol_norm) or pd.DataFrame()
        logging.warning("Liquidations not available for DEX")
        return pd.DataFrame()
        try:
            import ccxt
            ex = getattr(ccxt, exchange_name.lower(), ccxt.binance)()
            raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(raw, columns=["time", "open", "high", "low", "close", "volume"])
            df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True).dt.tz_localize(None)
            return df
        except Exception:
            return pd.DataFrame()

import pandas as pd

class DataCollector:
    def __init__(self):
        self.data = pd.DataFrame()

    def fetch_price(self, symbol: str):
        print(f"[DataCollector] Fetching price for {symbol}")
        return pd.DataFrame()  # Placeholder pour API exchange
