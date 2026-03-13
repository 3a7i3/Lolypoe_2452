from typing import Dict, List


def default_portfolio() -> Dict[str, float]:
    return {
        "BTC": 0.35,
        "ETH": 0.30,
        "SOL": 0.20,
        "AVAX": 0.15,
    }


def optimize_portfolio(top_symbols: List[str]) -> Dict[str, float]:
    if not top_symbols:
        return default_portfolio()

    weight = round(1.0 / len(top_symbols), 4)
    raw = {sym.replace("/USDT", ""): weight for sym in top_symbols}
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}
