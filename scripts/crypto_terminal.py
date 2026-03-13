import panel as pn
import pandas as pd
import ccxt
import hvplot.pandas
import ta

pn.extension()

# connexion Binance
exchange = ccxt.binance()

symbol = "BTC/USDT"
timeframe = "1m"
limit = 200

def get_data():

    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(
        ohlcv,
        columns=["timestamp","open","high","low","close","volume"]
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    # indicateurs
    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma50"] = df["close"].rolling(50).mean()

    return df


def trading_signal(df):

    last = df.iloc[-1]

    if last["rsi"] < 30 and last["ma20"] > last["ma50"]:
        return "BUY"

    elif last["rsi"] > 70 and last["ma20"] < last["ma50"]:
        return "SELL"

    else:
        return "HOLD"


def update():

    df = get_data()

    signal = trading_signal(df)

    chart = df.hvplot(
        x="timestamp",
        y=["close","ma20","ma50"],
        height=400,
        title=f"{symbol} price"
    )

    rsi_chart = df.hvplot(
        x="timestamp",
        y="rsi",
        height=200,
        title="RSI"
    )

    return pn.Column(
        f"# 🚀 Crypto Quant Bot",
        f"### Signal : **{signal}**",
        chart,
        rsi_chart,
        df.tail(10)
    )


dashboard = pn.Column(
    update()
).servable()