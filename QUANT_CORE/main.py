from data.collector import DataCollector
import logging

logging.basicConfig(level=logging.INFO, format='[Main] %(message)s')


def main():
    print("=== Data Engine MASSIF (CEX + DEX réel) ===")
    dc = DataCollector()

    symbols = ["BTC/USDT", "ETH/USDT"]  # DEX fonctionne sur tokens populaires
    sources = [
        ("cex", None),
        ("dex", "uniswap"),
        ("dex", "pancakeswap")
    ]
    timeframes = ["1d"]  # DEX subgraph daily

    for source, dex in sources:
        for symbol in symbols:
            for tf in timeframes:
                print(f"\n--- Fetch {symbol} | {source} | {tf} | {dex} ---")
                df = dc.fetch_ohlcv(symbol, source=source, timeframe=tf, save=True, dex_name=dex)
                print(f"Rows: {len(df)}")

    print("\n=== Done ===")
if __name__ == "__main__":
    main()from data.collector import DataCollector
from features.engineer import FeatureEngineer
from strategy.generator import StrategyGenerator
from interfaces.core_interface import CoreInterface

def main():
    dc = DataCollector()
    fe = FeatureEngineer()
    sg = StrategyGenerator()
    interface = CoreInterface(dc, fe, sg)

    df = interface.run_pipeline("BTCUSDT")
    print(df)

if __name__ == "__main__":
    main()