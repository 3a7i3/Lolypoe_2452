from __future__ import annotations

from statistics import mean

# Indicateurs trend-following → on suit la direction du marché
_TREND_INDICATORS = {"EMA", "MACD", "VWAP"}


def _real_returns(candles: list[dict]) -> list[float]:
    """Calcule les retours logarithmiques depuis les prix de clôture."""
    closes = [float(c["close"]) for c in candles]
    return [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1] != 0
    ]


def _apply_signal(returns: list[float], strategy: dict) -> list[float]:
    """Applique un signal simplifié selon le type de stratégie.

    - Trend-following (EMA, MACD, VWAP) : suit la direction du marché.
    - Mean-reversion (RSI, BOLLINGER, ATR) : fade les extrêmes.
    Le seuil de sensibilité vient du paramètre ``threshold`` de la stratégie.
    """
    indicator = strategy.get("entry_indicator", "EMA")
    # threshold est entre 0.2 et 2.5 dans le générateur ; on normalise en fraction de prix
    sensitivity = float(strategy.get("threshold", 0.5)) / 100.0

    if indicator in _TREND_INDICATORS:
        # Prend le trade seulement si le mouvement dépasse le seuil
        return [r if abs(r) >= sensitivity else 0.0 for r in returns]
    else:
        # Fade les extrêmes ; sous le seuil, suit le marché
        return [-r if abs(r) >= sensitivity else r for r in returns]


class BacktestLab:
    """Exécute des backtests sur données OHLCV réelles (ou synthétiques en fallback)."""

    def run_backtest(self, strategy: dict, data: list[dict]) -> dict:
        """Lance un backtest.

        Parameters
        ----------
        strategy:
            Paramètres de stratégie générés par ``StrategyGenerator``.
        data:
            Liste de bougies OHLCV. Si elle contient au moins 2 entrées avec
            des prix de clôture, les retours sont calculés depuis les vrais prix.
            Sinon, fallback sur des retours synthétiques reproductibles.
        """
        returns = _real_returns(data) if len(data) >= 2 else []

        if len(returns) >= 2:
            returns = _apply_signal(returns, strategy)
            data_mode = "real"
        else:
            # Fallback synthétique reproductible (préserve le comportement originel)
            import random  # noqa: PLC0415
            seed = abs(hash(str(strategy))) % (10**6)
            random.seed(seed)
            n = max(20, len(data) * 10)
            returns = [random.uniform(-0.02, 0.03) for _ in range(n)]
            data_mode = "synthetic"

        avg = mean(returns) if returns else 0.0
        variance = mean((r - avg) ** 2 for r in returns) if returns else 0.0
        vol = variance ** 0.5 if variance > 0 else 1e-9
        sharpe = (avg / vol) * (252 ** 0.5)

        equity = 1.0
        peak = 1.0
        max_dd = 0.0
        wins = 0
        for r in returns:
            equity *= 1 + r
            peak = max(peak, equity)
            dd = (peak - equity) / peak if peak else 0.0
            max_dd = max(max_dd, dd)
            if r > 0:
                wins += 1

        return {
            "strategy": strategy,
            "pnl": round((equity - 1.0) * 100, 4),
            "sharpe": round(sharpe, 4),
            "drawdown": round(max_dd, 4),
            "win_rate": round(wins / len(returns), 4) if returns else 0.0,
            "data_mode": data_mode,
            "candles_count": len(data),
        }
