import numpy as np
from quant.backtester import Backtester
from strategy_genome_engine import StrategyGenomeEngine

def strategy_to_signal(strategy, df):
    # Simple mapping: entry/exit to signal array
    # 1 = buy, -1 = sell, 0 = hold
    close = df["close"].values
    signals = np.zeros_like(close)
    # Example: momentum = buy if price > MA20
    if strategy["entry"] == "momentum":
        ma = pd.Series(close).rolling(20).mean().values
        signals[close > ma] = 1
    elif strategy["entry"] == "mean_reversion":
        ma = pd.Series(close).rolling(20).mean().values
        signals[close < ma] = 1
    elif strategy["entry"] == "breakout":
        high = pd.Series(close).rolling(20).max().values
        signals[close > high] = 1
    # Exit: simple rule
    if strategy["exit"] == "take_profit":
        signals[-1] = -1
    elif strategy["exit"] == "trailing_stop":
        signals[-5:] = -1
    elif strategy["exit"] == "mean_reversion_exit":
        ma = pd.Series(close).rolling(20).mean().values
        signals[close > ma] = -1
    return signals


if __name__ == "__main__":
    import pandas as pd
    # Mock data
    n = 300
    np.random.seed(42)
    prices = np.cumsum(np.random.randn(n)) + 100
    volumes = np.random.normal(1000, 200, n)
    df = pd.DataFrame({"close": prices, "volume": volumes})
    engine = StrategyGenomeEngine()
    strategies = engine.generate_population(50)
    backtester = Backtester()
    results = []
    for strat in strategies:
        signals = strategy_to_signal(strat, df)
        result = backtester.backtest(prices, signals)
        results.append({
            "strategy": strat,
            "total_return": result["total_return"],
            "sharpe": result["sharpe"]
        })
    # Sélectionne les 3 meilleures stratégies selon le total_return puis le Sharpe
    top = sorted(results, key=lambda x: (x["total_return"], x["sharpe"]), reverse=True)[:3]
    print("\nTop 3 stratégies :")
    for i, strat in enumerate(top, 1):
        print(f"#{i} - {strat['strategy']}\n  Total Return: {strat['total_return']:.2%}, Sharpe: {strat['sharpe']:.2f}\n")

    # Sauvegarde les meilleures stratégies dans un fichier JSON
    import json
    with open("top_strategies.json", "w", encoding="utf-8") as f:
        json.dump(top, f, indent=2, ensure_ascii=False)
    print("Top stratégies sauvegardées dans top_strategies.json")
