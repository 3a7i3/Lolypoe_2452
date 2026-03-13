import panel as pn
import pandas as pd
import ccxt
import hvplot.pandas
import ta

pn.extension()

exchange = ccxt.binance()

# cryptos à scanner
symbols = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "DOGE/USDT"
]

timeframe = "5m"
limit = 150


def get_data(symbol):

    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(
        ohlcv,
        columns=["timestamp","open","high","low","close","volume"]
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

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


def scan_market():

    results = []

    for symbol in symbols:

        try:

            df = get_data(symbol)

            signal = trading_signal(df)

            price = df["close"].iloc[-1]

            rsi = df["rsi"].iloc[-1]

            results.append({
                "symbol": symbol,
                "price": round(price,2),
                "rsi": round(rsi,2),
                "signal": signal
            })

        except Exception as e:

            print(symbol, e)

    return pd.DataFrame(results)


symbol_select = pn.widgets.Select(name="Crypto", options=symbols)


@pn.depends(symbol_select.param.value)
def update_dashboard(symbol):

    market = scan_market()

    df = get_data(symbol_select.value)

    chart = df.hvplot(
        x="timestamp",
        y=["close","ma20","ma50"],
        height=400,
        title=symbol_select.value
    )

    return pn.Column(
        "# 🚀 Crypto AI Market Scanner",
        "## Market signals",
        market,
        chart
    )


dashboard = pn.Column(
    symbol_select,
    update_dashboard
)

dashboard.servable()