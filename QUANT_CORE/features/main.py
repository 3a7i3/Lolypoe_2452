from data.collector import DataCollector
from features.engineer import FeatureEngineer
from data.utils import normalize_symbol

def main():
    print("=== Feature Engineering Test ===")
    dc = DataCollector()
    fe = FeatureEngineer()

    symbols = ["BTC/USDT", "ETH/USDT"]
    sources = ["cex", "dex"]
    timeframes = ["1h", "1d"]

    for source in sources:
        for symbol in symbols:
            for tf in timeframes:
                print(f"\n--- {symbol} | {source} | {tf} ---")
                df = dc.fetch_ohlcv(symbol, source=source, timeframe=tf, save=False)
                if df.empty:
                    print("No data fetched, skip")
                    continue

                df_features = fe.compute_features(df)
                fe.save_features(df_features, symbol, tf, source)
                print(df_features.tail())

    print("=== Feature Engineering Done ===")

if __name__ == "__main__":
    main()
