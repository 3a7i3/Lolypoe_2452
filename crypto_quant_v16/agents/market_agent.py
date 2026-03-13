from typing import Dict, List

import numpy as np


def collect_market_data(symbols: List[str]) -> List[Dict[str, float | str]]:
    rng = np.random.default_rng()
    data = []
    for symbol in symbols:
        price = float(rng.uniform(10.0, 70000.0))
        change_24h = float(rng.normal(0.0, 4.0))
        volume = float(rng.uniform(1e5, 2e9))
        data.append(
            {
                "symbol": symbol,
                "price": price,
                "change_24h": change_24h,
                "volume": volume,
            }
        )
    return data
