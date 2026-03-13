import yfinance as yf

def get_market_data(symbol="BTC-USD", interval="1m", period="1d"):

    data = yf.download(
        tickers=symbol,
        interval=interval,
        period=period
    )

    return data