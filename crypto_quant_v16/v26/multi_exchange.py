from __future__ import annotations

import random
from typing import Dict, Tuple


def scan_prices(symbol: str, exchanges: list[str], anchor_price: float) -> Dict[str, float]:
    prices = {}
    for ex in exchanges:
        noise = random.uniform(-0.004, 0.004)
        prices[ex] = round(anchor_price * (1 + noise), 2)
    return prices


def detect_arbitrage(prices: Dict[str, float]) -> Tuple[str, str, float]:
    buy_ex = min(prices, key=prices.get)
    sell_ex = max(prices, key=prices.get)
    spread = round(prices[sell_ex] - prices[buy_ex], 2)
    return buy_ex, sell_ex, spread
