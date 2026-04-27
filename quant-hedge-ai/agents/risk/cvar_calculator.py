"""Option M — CVaR (Conditional Value at Risk).

CVaR (également appelé Expected Shortfall) mesure la perte moyenne
au-delà du quantile VaR. C'est un complément naturel au Kelly Criterion :
Kelly optimise la taille de position, CVaR limite le risque extrême.

Formule :
    VaR_α  = quantile(1 - α) des pertes
    CVaR_α = moyenne des pertes >= VaR_α

Les retours sont fournis en valeurs décimales (ex: -0.03 = -3%).
Les pertes sont des valeurs positives dans la sortie.
"""
from __future__ import annotations

import statistics
from typing import Sequence


class CVaRCalculator:
    """Calcule le CVaR (Expected Shortfall) à partir d'une liste de retours.

    Args:
        confidence: niveau de confiance, ex. 0.95 signifie que CVaR
                    mesure la perte moyenne dans le pire 5% des cas.
        max_loss:   seuil de perte acceptable (fraction du capital).
                    ``is_within_limit`` retourne False si CVaR > max_loss.

    Raises:
        ValueError: si confidence n'est pas dans ]0, 1[.
        ValueError: si max_loss <= 0.
    """

    def __init__(self, confidence: float = 0.95, max_loss: float = 0.05) -> None:
        if not (0.0 < confidence < 1.0):
            raise ValueError(f"confidence doit être dans ]0, 1[, reçu: {confidence}")
        if max_loss <= 0.0:
            raise ValueError(f"max_loss doit être > 0, reçu: {max_loss}")

        self.confidence = confidence
        self.max_loss = max_loss

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def compute(self, returns: Sequence[float]) -> float:
        """Calcule le CVaR depuis une liste de retours.

        Returns:
            CVaR exprimé en perte positive (ex. 0.04 = 4% de perte attendue
            dans le pire tail). Retourne 0.0 si la liste est trop courte.
        """
        if len(returns) < 2:
            return 0.0

        sorted_returns = sorted(returns)  # tri croissant → pires en tête
        n = len(sorted_returns)

        # Nombre de points dans le tail (pire (1 - confidence) %)
        tail_count = max(1, int(n * (1.0 - self.confidence)))
        tail = sorted_returns[:tail_count]

        avg_tail = sum(tail) / len(tail)
        # CVaR = perte (valeur positive) → on prend l'opposé
        return max(0.0, -avg_tail)

    def is_within_limit(self, returns: Sequence[float]) -> bool:
        """Retourne True si CVaR <= max_loss (risque acceptable)."""
        return self.compute(returns) <= self.max_loss

    def compute_var(self, returns: Sequence[float]) -> float:
        """VaR au seuil de confiance (quantile simple).

        Returns:
            VaR exprimée en perte positive. 0.0 si données insuffisantes.
        """
        if len(returns) < 2:
            return 0.0
        sorted_returns = sorted(returns)
        idx = max(0, int(len(sorted_returns) * (1.0 - self.confidence)) - 1)
        return max(0.0, -sorted_returns[idx])

    def summary(self, returns: Sequence[float]) -> dict[str, float]:
        """Retourne un résumé complet : VaR, CVaR, worst_return, std."""
        if not returns:
            return {"var": 0.0, "cvar": 0.0, "worst_return": 0.0, "std": 0.0}
        return {
            "var": round(self.compute_var(returns), 6),
            "cvar": round(self.compute(returns), 6),
            "worst_return": round(min(returns), 6),
            "std": round(statistics.pstdev(returns), 6) if len(returns) >= 2 else 0.0,
        }
