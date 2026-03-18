import pandas as pd
import yfinance as yf
import investpy

class MarketDataLoader:
    def load_yahoo(self, symbol="BTC-USD", interval="1h", lookback="30d"):
        df = yf.download(symbol, period=lookback, interval=interval)
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        df["rsi"] = (df["close"] - df["close"].rolling(14).mean()) / df["close"].rolling(14).std()
        df["momentum"] = df["close"].diff(4)
        df["volatility"] = df["close"].rolling(10).std()
        df["macd"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
        df["ema"] = df["close"].ewm(span=10).mean()
        df["sma"] = df["close"].rolling(10).mean()
        df["stochastic"] = (df["close"] - df["low"].rolling(14).min()) / (df["high"].rolling(14).max() - df["low"].rolling(14).min())
        df["adx"] = df["high"].rolling(14).std() / df["low"].rolling(14).std()
        df["obv"] = (df["volume"] * ((df["close"] > df["close"].shift(1)).astype(int) - (df["close"] < df["close"].shift(1)).astype(int))).cumsum()
        df = df.dropna()
        return df.reset_index(drop=True)

    def load_investpy_stock(self, symbol="AAPL", country="united states", interval="Daily", n=90):
        df = investpy.stocks.get_stock_historical_data(stock=symbol, country=country, from_date="01/01/2023", to_date="01/04/2023", interval=interval)
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        df["rsi"] = (df["close"] - df["close"].rolling(14).mean()) / df["close"].rolling(14).std()
        df["momentum"] = df["close"].diff(4)
        df["volatility"] = df["close"].rolling(10).std()
        df["macd"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
        df["ema"] = df["close"].ewm(span=10).mean()
        df["sma"] = df["close"].rolling(10).mean()
        df["stochastic"] = (df["close"] - df["low"].rolling(14).min()) / (df["high"].rolling(14).max() - df["low"].rolling(14).min())
        df["adx"] = df["high"].rolling(14).std() / df["low"].rolling(14).std()
        df["obv"] = (df["volume"] * ((df["close"] > df["close"].shift(1)).astype(int) - (df["close"] < df["close"].shift(1)).astype(int))).cumsum()
        df = df.dropna()
        return df.reset_index(drop=True)

    def load_investpy_crypto(self, symbol="bitcoin", interval="Daily", n=90):
        df = investpy.crypto.get_crypto_historical_data(crypto=symbol, from_date="01/01/2023", to_date="01/04/2023", interval=interval)
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        df["rsi"] = (df["close"] - df["close"].rolling(14).mean()) / df["close"].rolling(14).std()
        df["momentum"] = df["close"].diff(4)
        df["volatility"] = df["close"].rolling(10).std()
        df["macd"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
        df["ema"] = df["close"].ewm(span=10).mean()
        df["sma"] = df["close"].rolling(10).mean()
        df["stochastic"] = (df["close"] - df["low"].rolling(14).min()) / (df["high"].rolling(14).max() - df["low"].rolling(14).min())
        df["adx"] = df["high"].rolling(14).std() / df["low"].rolling(14).std()
        df["obv"] = (df["volume"] * ((df["close"] > df["close"].shift(1)).astype(int) - (df["close"] < df["close"].shift(1)).astype(int))).cumsum()
        df = df.dropna()
        return df.reset_index(drop=True)
