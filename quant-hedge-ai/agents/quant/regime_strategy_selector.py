"""Option W — Regime-Aware Strategy Selector.

Sélectionne les stratégies adaptées au régime de marché courant
(bull / bear / sideways / volatile) parmi la liste évoluée.

Règles par défaut :
    bull      → favorise les stratégies trend-following (EMA, MACD, VWAP)
    bear      → favorise mean-reversion + position courte (RSI suracheté, BB)
    sideways  → favorise mean-reversion (RSI, Stoch)
    volatile  → réduit l'exposition, favorise les stratégies à faible signal

Workflow dans main_v91.py (après `regime = regime_detector.detect(...)`) :
    selector = RegimeStrategySelector()
    selected = selector.select(evolved, regime=regime, top_n=cfg.population_size)
    # → liste filtrée/reordonnée pour le BacktestLab
"""
from __future__ import annotations

from typing import Any

# Indicateurs typiquement trend-following
_TREND_INDICATORS = {"EMA", "MACD", "VWAP", "ADX", "SMA", "MOMENTUM"}
# Indicateurs typiquement mean-reversion
_MEAN_INDICATORS = {"RSI", "STOCH", "BB", "CCI", "WILLIAMS_R", "MEAN_REVERSION"}


def _indicator_family(strategy: dict) -> str:
    """Retourne 'trend' | 'mean' | 'unknown'."""
    ind = str(strategy.get("entry_indicator", "")).upper()
    if ind in _TREND_INDICATORS:
        return "trend"
    if ind in _MEAN_INDICATORS:
        return "mean"
    return "unknown"


def _regime_score(strategy: dict, regime: str) -> float:
    """Score de compatibilité [0, 1] entre stratégie et régime.

    Plus le score est haut, plus la stratégie est adaptée.
    """
    family = _indicator_family(strategy)
    regime_lower = regime.lower()

    # Table de compatibilité
    compat = {
        "bull":      {"trend": 1.0, "mean": 0.3, "unknown": 0.5},
        "bear":      {"trend": 0.4, "mean": 0.8, "unknown": 0.5},
        "sideways":  {"trend": 0.3, "mean": 1.0, "unknown": 0.5},
        "volatile":  {"trend": 0.5, "mean": 0.5, "unknown": 0.5},
        "neutral":   {"trend": 0.6, "mean": 0.6, "unknown": 0.6},
    }

    row = compat.get(regime_lower, compat["neutral"])
    return row.get(family, 0.5)


class RegimeStrategySelector:
    """Filtre et réordonne les stratégies en fonction du régime.

    Args:
        min_score:      score de compatibilité minimum pour inclure une stratégie
                        (ex. 0.3 = inclure si >= 30% compatible).
        boost_factor:   multiplicateur de sharpe pour les stratégies très compatibles
                        (score >= 0.8) lors du tri.

    Raises:
        ValueError: si un paramètre est invalide.
    """

    def __init__(
        self,
        min_score: float = 0.25,
        boost_factor: float = 1.5,
    ) -> None:
        if not (0.0 <= min_score <= 1.0):
            raise ValueError(f"min_score doit être dans [0, 1], reçu: {min_score}")
        if boost_factor <= 0:
            raise ValueError(f"boost_factor doit être > 0, reçu: {boost_factor}")

        self.min_score = min_score
        self.boost_factor = boost_factor

    def score_strategy(self, strategy: dict, regime: str) -> float:
        """Retourne le score de compatibilité [0, 1]."""
        return _regime_score(strategy, regime)

    def select(
        self,
        strategies: list[dict[str, Any]],
        regime: str,
        top_n: int | None = None,
    ) -> list[dict[str, Any]]:
        """Filtre et trie les stratégies selon leur compatibilité avec le régime.

        Args:
            strategies: liste de dicts stratégie (avec 'entry_indicator', optionnel 'sharpe').
            regime:     régime courant ('bull', 'bear', 'sideways', 'volatile', 'neutral').
            top_n:      nombre max de stratégies à retourner (None = toutes).

        Returns:
            Sous-liste triée par score descendant, taille <= top_n.
        """
        if not strategies:
            return []

        scored: list[tuple[float, dict]] = []
        for strat in strategies:
            score = _regime_score(strat, regime)
            if score < self.min_score:
                continue

            # Boost les stratégies très compatibles lors du tri
            base_sharpe = float(strat.get("sharpe", 0.0))
            effective_score = score * (self.boost_factor if score >= 0.8 else 1.0) + base_sharpe * 0.1
            scored.append((effective_score, strat))

        scored.sort(key=lambda x: x[0], reverse=True)

        result = [s for _, s in scored]
        if top_n is not None and top_n > 0:
            result = result[:top_n]

        # Si le filtre a tout éliminé, retourner toutes les stratégies non filtrées
        if not result and strategies:
            return strategies[:top_n] if top_n else strategies

        return result

    def summary(self, strategies: list[dict], regime: str) -> dict:
        """Résumé de la sélection pour le dashboard.

        Returns:
            Dict avec counts par famille et régime courant.
        """
        trend_count = sum(1 for s in strategies if _indicator_family(s) == "trend")
        mean_count = sum(1 for s in strategies if _indicator_family(s) == "mean")
        unknown_count = len(strategies) - trend_count - mean_count

        return {
            "regime": regime,
            "total": len(strategies),
            "trend_following": trend_count,
            "mean_reversion": mean_count,
            "unknown": unknown_count,
            "regime_optimal_family": (
                "trend" if regime.lower() in ("bull",) else
                "mean" if regime.lower() in ("bear", "sideways") else
                "mixed"
            ),
        }
