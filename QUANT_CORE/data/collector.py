"""
DataCollector stub for QUANT_CORE
"""
class DataCollector:
    def __init__(self):
        pass

    def scan_market(self, symbols, interval="1h", period="6mo", min_volume=10000):
        """Scanne le marché pour tous les symboles."""
        import yfinance as yf
        import pandas as pd
        market_data = {}
        for symbol in symbols:
            try:
                data = self.fetch_market_data(symbol, interval=interval, period=period)
                if data is not None and not data.empty and len(data) > 0:
                    recent_volume = data['Volume'].iloc[-1]
                    if recent_volume >= min_volume:
                        market_data[symbol] = data
                else:
                    pass  # log warning
            except Exception:
                pass  # log error
        return market_data

    def fetch_market_data(self, symbol, interval="1h", period="6mo"):
        """Récupère les données de marché avec yfinance."""
        import yfinance as yf
        import pandas as pd
        try:
            data = yf.download(
                tickers=symbol,
                interval=interval,
                period=period,
                progress=False
            )
            if data is None or data.empty:
                return None
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            data.columns = data.columns.str.upper()
            required_cols = ['CLOSE', 'HIGH', 'LOW', 'VOLUME']
            if not all(col in data.columns for col in required_cols):
                return None
            data = data.rename(columns={
                'CLOSE': 'Close',
                'HIGH': 'High',
                'LOW': 'Low',
                'OPEN': 'Open',
                'VOLUME': 'Volume'
            })
            return data
        except Exception:
            return None

    def fetch_ohlcv(self, symbol="BTC/USDT", timeframe="1h", limit=220, exchange_name="binance", data_mode="auto"):
        """Fetch OHLCV candles (ccxt, mock, DEX, REST, WebSocket)."""
        import pandas as pd
        try:
            import ccxt
            ex = getattr(ccxt, exchange_name.lower(), ccxt.binance)()
            raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(raw, columns=["time", "open", "high", "low", "close", "volume"])
            df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True).dt.tz_localize(None)
            return df
        except Exception:
            return pd.DataFrame()
