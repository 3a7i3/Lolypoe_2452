"""Kelly Criterion — Calcul dynamique de la taille de position optimale.

Formule de Kelly : f* = W - (1 - W) / R
  - W  = win rate (fraction de trades gagnants)
  - R  = payoff ratio = avg_win / avg_loss (ratio gain moyen / perte moyenne)

On utilise généralement la Half-Kelly (f*/2) pour réduire la variance et la
sensibilité aux erreurs d'estimation. La fraction est ensuite clampée dans
[0, max_fraction] pour éviter le surdimensionnement.

Exemple d'usage :
    kelly = KellyCriterion(max_fraction=0.25, half_kelly=True)
    size = kelly.compute_size(win_rate=0.55, avg_win=0.03, avg_loss=0.015)
    # → ~0.125 (12.5% du capital sur ce trade)
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_MIN_PAYOFF = 1e-9  # évite division par zéro dans le ratio


class KellyCriterion:
    """Calcule la taille de position optimale selon le critère de Kelly.

    Paramètres
    ----------
    max_fraction:
        Fraction maximale autorisée du capital (défaut : 0.25 → 25%).
        Agit comme garde-fou même si Kelly suggère davantage.
    half_kelly:
        Si True (défaut), divise par 2 la fraction brute de Kelly pour
        réduire la variance et la sensibilité aux erreurs d'estimation.
    """

    def __init__(self, max_fraction: float = 0.25, half_kelly: bool = True) -> None:
        if max_fraction <= 0 or max_fraction > 1.0:
            raise ValueError(f"max_fraction doit être dans ]0, 1] — reçu {max_fraction}")
        self.max_fraction = max_fraction
        self.half_kelly = half_kelly

    # ------------------------------------------------------------------
    # Formule brute
    # ------------------------------------------------------------------

    def raw_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Fraction de Kelly brute sans clamp ni half-Kelly.

        Retourne 0.0 si les paramètres sont invalides ou si Kelly est négatif
        (stratégie non rentable selon la formule).

        Paramètres
        ----------
        win_rate:
            Taux de succès ∈ [0, 1].
        avg_win:
            Gain moyen par trade gagnant (valeur absolue, > 0).
        avg_loss:
            Perte moyenne par trade perdant (valeur absolue, > 0).
        """
        if not (0.0 < win_rate < 1.0):
            return 0.0
        if avg_loss <= 0 or avg_win <= 0:
            return 0.0

        payoff_ratio = avg_win / max(avg_loss, _MIN_PAYOFF)
        loss_rate = 1.0 - win_rate
        kelly = win_rate - (loss_rate / payoff_ratio)
        return max(0.0, kelly)

    # ------------------------------------------------------------------
    # Fraction ajustée (half + clamp)
    # ------------------------------------------------------------------

    def adjusted_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Fraction Kelly ajustée : half-Kelly si activé, puis clamp à max_fraction."""
        raw = self.raw_fraction(win_rate, avg_win, avg_loss)
        fraction = raw / 2.0 if self.half_kelly else raw
        clamped = min(fraction, self.max_fraction)
        logger.debug(
            "KellyCriterion: win_rate=%.3f avg_win=%.4f avg_loss=%.4f "
            "→ raw=%.4f adjusted=%.4f clamped=%.4f",
            win_rate, avg_win, avg_loss, raw, fraction, clamped,
        )
        return round(clamped, 6)

    # ------------------------------------------------------------------
    # Point d'entrée principal
    # ------------------------------------------------------------------

    def compute_size(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        fallback: float = 0.02,
    ) -> float:
        """Retourne la fraction du capital à allouer pour ce trade.

        Si Kelly est nul (stratégie non rentable) ou invalide, retourne
        ``fallback`` (ex: la limite de risque par défaut depuis la config).

        Paramètres
        ----------
        win_rate:
            Taux de succès estimé du backtest.
        avg_win:
            Gain moyen par trade gagnant.
        avg_loss:
            Perte moyenne par trade perdant.
        fallback:
            Fraction à utiliser si Kelly = 0 (défaut : 2%).
        """
        fraction = self.adjusted_fraction(win_rate, avg_win, avg_loss)
        if fraction <= 0.0:
            logger.debug(
                "KellyCriterion: fraction=0 (stratégie non rentable) — fallback=%.4f", fallback
            )
            return min(fallback, self.max_fraction)
        return fraction


def compute_avg_win_loss(returns: list[float]) -> tuple[float, float]:
    """Calcule avg_win et avg_loss depuis une liste de retours.

    Retourne (avg_win, avg_loss) avec des valeurs absolues positives.
    Si aucun gain ou aucune perte n'est présent, retourne 0.0 pour la valeur manquante.
    """
    gains = [r for r in returns if r > 0]
    losses = [abs(r) for r in returns if r < 0]
    avg_win = sum(gains) / len(gains) if gains else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    return avg_win, avg_loss
