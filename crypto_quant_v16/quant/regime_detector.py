from typing import Sequence

import numpy as np


def detect_regime(prices: Sequence[float]) -> str:
    arr = np.asarray(prices, dtype=float)
    if arr.size < 2:
        return "NORMAL"

    volatility = float(np.std(arr))
    trend = float(arr[-1] - arr[0])

    if volatility > 0.05:
        return "HIGH_VOL"
    if trend > 0:
        return "BULL"
    return "BEAR"
