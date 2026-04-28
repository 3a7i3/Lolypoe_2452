"""Option U — Walk-Forward Optimization (WFO).

Divise l'historique en N fenêtres train/test glissantes pour mesurer
la stabilité out-of-sample d'une stratégie et détecter l'overfitting.

Workflow :
    wfo = WalkForwardOptimizer(n_splits=5, train_ratio=0.7)
    result = wfo.run(strategy, data)
    # → {
    #     "oos_sharpes": [0.8, 1.1, 0.5, ...],
    #     "mean_sharpe": 0.8,
    #     "stability":   0.72,   # % de splits profitable OOS
    #     "mean_drawdown": 0.04,
    #     "n_splits_used": 5,
    #     "data_mode": "real" | "insufficient",
    # }
"""
from __future__ import annotations

import math
from statistics import mean, stdev
from typing import Any


def _returns_from_candles(candles: list[dict]) -> list[float]:
    """Retours simples depuis prix de clôture."""
    closes = [float(c["close"]) for c in candles]
    return [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1] != 0
    ]


def _apply_signal(returns: list[float], strategy: dict) -> list[float]:
    """Applique le signal de la stratégie (même logique que BacktestLab)."""
    _TREND = {"EMA", "MACD", "VWAP"}
    indicator = strategy.get("entry_indicator", "EMA")
    sensitivity = float(strategy.get("threshold", 0.5)) / 100.0
    if indicator in _TREND:
        return [r if abs(r) >= sensitivity else 0.0 for r in returns]
    return [-r if abs(r) >= sensitivity else r for r in returns]


def _metrics(returns: list[float]) -> dict[str, float]:
    """Calcule sharpe, drawdown, win_rate depuis une liste de retours."""
    if not returns:
        return {"sharpe": 0.0, "drawdown": 0.0, "win_rate": 0.0, "pnl": 0.0}

    avg = mean(returns)
    variance = mean((r - avg) ** 2 for r in returns)
    vol = math.sqrt(variance) if variance > 0 else 1e-9
    sharpe = (avg / vol) * math.sqrt(252)

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
        "sharpe": round(sharpe, 4),
        "drawdown": round(max_dd, 4),
        "win_rate": round(wins / len(returns), 4),
        "pnl": round((equity - 1.0) * 100, 4),
    }


class WalkForwardOptimizer:
    """Optimisation walk-forward pour mesurer la robustesse out-of-sample.

    Args:
        n_splits:    nombre de fenêtres train/test (minimum 2).
        train_ratio: fraction de chaque fenêtre utilisée pour l'entraînement
                     (ex. 0.7 = 70% train, 30% test OOS).
        min_oos_bars: nombre minimum de barres OOS par split pour valider.

    Raises:
        ValueError: si les paramètres sont invalides.
    """

    def __init__(
        self,
        n_splits: int = 5,
        train_ratio: float = 0.7,
        min_oos_bars: int = 10,
    ) -> None:
        if n_splits < 2:
            raise ValueError(f"n_splits doit être >= 2, reçu: {n_splits}")
        if not (0.1 <= train_ratio <= 0.95):
            raise ValueError(f"train_ratio doit être dans [0.1, 0.95], reçu: {train_ratio}")
        if min_oos_bars < 1:
            raise ValueError(f"min_oos_bars doit être >= 1, reçu: {min_oos_bars}")

        self.n_splits = n_splits
        self.train_ratio = train_ratio
        self.min_oos_bars = min_oos_bars

    def _make_splits(
        self, data: list[dict]
    ) -> list[tuple[list[dict], list[dict]]]:
        """Découpe les données en paires (train, test) glissantes.

        Méthode : expanding window — la fenêtre de test avance d'un pas
        égal à ``len(data) // n_splits``.

        Returns:
            Liste de (train_candles, test_candles).
        """
        n = len(data)
        step = n // (self.n_splits + 1)
        if step < 2:
            return []

        splits: list[tuple[list[dict], list[dict]]] = []
        for i in range(1, self.n_splits + 1):
            end = min(i * step + step, n)
            split_end = i * step
            train = data[:split_end]
            test = data[split_end:end]
            if len(test) >= self.min_oos_bars:
                splits.append((train, test))

        return splits

    def run(self, strategy: dict[str, Any], data: list[dict]) -> dict[str, Any]:
        """Lance le walk-forward sur la stratégie avec les données fournies.

        Args:
            strategy: paramètres de stratégie (même format que BacktestLab).
            data:     liste de bougies OHLCV historiques.

        Returns:
            Dict avec :
            - ``oos_sharpes``   : liste des Sharpe OOS par split
            - ``oos_drawdowns`` : liste des drawdowns OOS par split
            - ``oos_win_rates`` : liste des win rates OOS par split
            - ``mean_sharpe``   : moyenne Sharpe OOS
            - ``stability``     : fraction de splits avec Sharpe OOS > 0
            - ``mean_drawdown`` : drawdown OOS moyen
            - ``n_splits_used`` : nombre de splits effectivement évalués
            - ``data_mode``     : ``"real"`` ou ``"insufficient"``
        """
        splits = self._make_splits(data)
        if not splits:
            return {
                "oos_sharpes": [],
                "oos_drawdowns": [],
                "oos_win_rates": [],
                "mean_sharpe": 0.0,
                "stability": 0.0,
                "mean_drawdown": 0.0,
                "n_splits_used": 0,
                "data_mode": "insufficient",
            }

        oos_metrics: list[dict[str, float]] = []
        for _train, test in splits:
            returns_oos = _returns_from_candles(test)
            if len(returns_oos) < 2:
                continue
            signal_returns = _apply_signal(returns_oos, strategy)
            m = _metrics(signal_returns)
            oos_metrics.append(m)

        if not oos_metrics:
            return {
                "oos_sharpes": [],
                "oos_drawdowns": [],
                "oos_win_rates": [],
                "mean_sharpe": 0.0,
                "stability": 0.0,
                "mean_drawdown": 0.0,
                "n_splits_used": 0,
                "data_mode": "insufficient",
            }

        sharpes = [m["sharpe"] for m in oos_metrics]
        drawdowns = [m["drawdown"] for m in oos_metrics]
        win_rates = [m["win_rate"] for m in oos_metrics]

        mean_sharpe = mean(sharpes)
        stability = sum(1 for s in sharpes if s > 0) / len(sharpes)
        mean_drawdown = mean(drawdowns)

        # Consistance : écart-type des Sharpe (faible = plus stable)
        sharpe_std = stdev(sharpes) if len(sharpes) >= 2 else 0.0

        return {
            "oos_sharpes": [round(s, 4) for s in sharpes],
            "oos_drawdowns": [round(d, 4) for d in drawdowns],
            "oos_win_rates": [round(w, 4) for w in win_rates],
            "mean_sharpe": round(mean_sharpe, 4),
            "stability": round(stability, 4),
            "mean_drawdown": round(mean_drawdown, 4),
            "sharpe_std": round(sharpe_std, 4),
            "n_splits_used": len(oos_metrics),
            "data_mode": "real",
        }

    def is_robust(
        self,
        result: dict[str, Any],
        min_stability: float = 0.6,
        min_mean_sharpe: float = 0.5,
    ) -> bool:
        """Retourne True si la stratégie passe les critères de robustesse WFO.

        Args:
            result:           retour de ``run()``.
            min_stability:    fraction minimale de splits OOS > 0.
            min_mean_sharpe:  Sharpe OOS moyen minimum.
        """
        if result["data_mode"] == "insufficient":
            return False
        return (
            result["stability"] >= min_stability
            and result["mean_sharpe"] >= min_mean_sharpe
        )
